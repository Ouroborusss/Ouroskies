# SPDX-License-Identifier: GPL-3.0-or-later

"""OuroSkies World lifecycle and minimal Multiple Scattering sky graph."""

from __future__ import annotations

import bpy

from . import defaults


def stop_handlers() -> None:
    """Frame handler stays registered; place/date evaluate no-ops when disabled."""
    from . import place_date

    place_date.stop_handlers()


def find_ouroskies_world(scene: bpy.types.Scene) -> bpy.types.World | None:
    world = scene.world
    if world is not None and world.get(defaults.WORLD_OWNED_KEY):
        return world
    for candidate in bpy.data.worlds:
        if candidate.get(defaults.WORLD_OWNED_KEY):
            return candidate
    return None


def find_sky_node(world: bpy.types.World) -> bpy.types.ShaderNodeTexSky | None:
    if world is None or world.node_tree is None:
        return None
    node = world.node_tree.nodes.get(defaults.NODE_SKY)
    if isinstance(node, bpy.types.ShaderNodeTexSky):
        return node
    for candidate in world.node_tree.nodes:
        if isinstance(candidate, bpy.types.ShaderNodeTexSky):
            return candidate
    return None


def apply_atmosphere_to_sky(
    sky: bpy.types.ShaderNodeTexSky,
    settings: bpy.types.PropertyGroup,
) -> None:
    sky.sky_type = "MULTIPLE_SCATTERING"
    sky.air_density = settings.air
    sky.aerosol_density = settings.dust
    sky.ozone_density = settings.ozone
    sky.altitude = settings.altitude


def apply_settings_to_sky(
    sky: bpy.types.ShaderNodeTexSky,
    settings: bpy.types.PropertyGroup,
) -> None:
    """Push atmosphere + current aim mode onto a Sky Texture node."""
    from . import aim, celestials

    apply_atmosphere_to_sky(sky, settings)
    celestials.apply_sun_size_punch_to_sky(sky, settings)
    if settings.aim_mode == "MANUAL":
        aim.apply_manual_aim_to_sky(sky, settings)


def sync_atmosphere(scene: bpy.types.Scene) -> None:
    """Push Scene atmosphere props onto the active OuroSkies Sky Texture."""
    settings = scene.ouroskies
    if not settings.is_enabled:
        return
    world = find_ouroskies_world(scene)
    if world is None:
        return
    sky = find_sky_node(world)
    if sky is None:
        return
    apply_atmosphere_to_sky(sky, settings)


def rebuild_sky_graph(world: bpy.types.World, settings: bpy.types.PropertyGroup) -> None:
    """Author canonical Looks tree: Sky → WB → camera/light strengths → airglow → Output."""
    from . import looks

    world.use_nodes = True
    node_tree = world.node_tree
    node_tree.nodes.clear()

    sky = node_tree.nodes.new("ShaderNodeTexSky")
    sky.name = defaults.NODE_SKY
    sky.label = defaults.NODE_SKY
    sky.location = (-700.0, 0.0)
    sky.sky_type = "MULTIPLE_SCATTERING"
    apply_settings_to_sky(sky, settings)

    wb_color = node_tree.nodes.new("ShaderNodeRGB")
    wb_color.name = defaults.NODE_WB_COLOR
    wb_color.label = defaults.NODE_WB_COLOR
    wb_color.location = (-700.0, -220.0)

    wb_mix = node_tree.nodes.new("ShaderNodeMix")
    wb_mix.name = defaults.NODE_WB_MIX
    wb_mix.label = defaults.NODE_WB_MIX
    wb_mix.location = (-480.0, 0.0)
    wb_mix.data_type = "RGBA"
    wb_mix.blend_type = "MULTIPLY"
    wb_mix.inputs["Factor"].default_value = 1.0

    bg_cam = node_tree.nodes.new("ShaderNodeBackground")
    bg_cam.name = defaults.NODE_BG_CAMERA
    bg_cam.label = "Sky Strength (camera)"
    bg_cam.location = (-240.0, 80.0)

    bg_light = node_tree.nodes.new("ShaderNodeBackground")
    bg_light.name = defaults.NODE_BG_LIGHT
    bg_light.label = "World Contribution (GI)"
    bg_light.location = (-240.0, -80.0)

    light_path = node_tree.nodes.new("ShaderNodeLightPath")
    light_path.name = defaults.NODE_LIGHT_PATH
    light_path.label = defaults.NODE_LIGHT_PATH
    light_path.location = (-240.0, 240.0)

    mix_cam = node_tree.nodes.new("ShaderNodeMixShader")
    mix_cam.name = defaults.NODE_MIX_CAMERA
    mix_cam.label = defaults.NODE_MIX_CAMERA
    mix_cam.location = (0.0, 40.0)

    glow_color = node_tree.nodes.new("ShaderNodeRGB")
    glow_color.name = defaults.NODE_AIRGLOW_COLOR
    glow_color.label = defaults.NODE_AIRGLOW_COLOR
    glow_color.location = (-240.0, -260.0)

    bg_glow = node_tree.nodes.new("ShaderNodeBackground")
    bg_glow.name = defaults.NODE_BG_AIRGLOW
    bg_glow.label = defaults.NODE_BG_AIRGLOW
    bg_glow.location = (0.0, -220.0)

    add_glow = node_tree.nodes.new("ShaderNodeAddShader")
    add_glow.name = defaults.NODE_ADD_AIRGLOW
    add_glow.label = defaults.NODE_ADD_AIRGLOW
    add_glow.location = (220.0, 0.0)

    output = node_tree.nodes.new("ShaderNodeOutputWorld")
    output.name = defaults.NODE_OUTPUT
    output.label = defaults.NODE_OUTPUT
    output.location = (440.0, 0.0)
    output.is_active_output = True
    output.target = "ALL"

    links = node_tree.links
    links.new(sky.outputs["Color"], wb_mix.inputs["A"])
    links.new(wb_color.outputs["Color"], wb_mix.inputs["B"])
    # Prefer typed Color sockets when present (Blender 4+/5 Mix node).
    result = wb_mix.outputs.get("Result_Color") or wb_mix.outputs.get("Result")
    links.new(result, bg_cam.inputs["Color"])
    links.new(result, bg_light.inputs["Color"])
    links.new(light_path.outputs["Is Camera Ray"], mix_cam.inputs["Factor"])
    links.new(bg_light.outputs["Background"], mix_cam.inputs[1])
    links.new(bg_cam.outputs["Background"], mix_cam.inputs[2])

    from . import celestials, stars

    # Binary sun: camera-look Background Add after sky mix (Strength = appearance).
    sky_with_binary = celestials.wire_binary_sun_nodes(
        node_tree,
        light_path,
        mix_cam.outputs["Shader"],
    )
    links.new(sky_with_binary, add_glow.inputs[0])
    links.new(glow_color.outputs["Color"], bg_glow.inputs["Color"])
    links.new(bg_glow.outputs["Background"], add_glow.inputs[1])
    # Stars + Milky after airglow (airglow sits behind the field).
    sky_with_stars = stars.wire_stars_nodes(
        node_tree,
        light_path,
        add_glow.outputs["Shader"],
    )
    links.new(sky_with_stars, output.inputs["Surface"])

    if hasattr(sky, "sun_disc"):
        sky.sun_disc = True
    sky.texture_mapping.rotation = (0.0, 0.0, 0.0)

    looks.sync_looks_to_world(settings, world)
    celestials.sync_binary_sun_to_world(settings, world)
    stars.sync_stars_to_world(settings, world)


def _unique_world_name() -> str:
    base = defaults.WORLD_NAME
    if base not in bpy.data.worlds:
        return base
    index = 1
    while f"{base}.{index:03d}" in bpy.data.worlds:
        index += 1
    return f"{base}.{index:03d}"


def _fallback_world(exclude: bpy.types.World | None) -> bpy.types.World:
    """Pick a World to restore when the remembered previous World is gone.

    provisional: name-pointer only; if missing, use any non-owned World, else a fresh default.
    """
    for candidate in bpy.data.worlds:
        if candidate is exclude:
            continue
        if candidate.get(defaults.WORLD_OWNED_KEY):
            continue
        return candidate
    world = bpy.data.worlds.new("World")
    return world


def enable(scene: bpy.types.Scene) -> bpy.types.World:
    """Create OuroSkies World, remember previous, switch scene, build sky graph."""
    settings = scene.ouroskies
    existing = find_ouroskies_world(scene)
    if settings.is_enabled and existing is not None and scene.world == existing:
        rebuild_sky_graph(existing, settings)
        from . import lamps, looks

        looks.sync_looks(scene)
        if settings.aim_mode == "PLACE_DATE":
            from . import place_date

            place_date.evaluate(scene)
        from . import celestials

        celestials.sync_celestials(scene)
        lamps.sync_lamps(scene)
        return existing

    previous = scene.world
    settings.previous_world_name = previous.name if previous is not None else ""

    world = bpy.data.worlds.new(_unique_world_name())
    world[defaults.WORLD_OWNED_KEY] = True
    rebuild_sky_graph(world, settings)
    scene.world = world
    settings.is_enabled = True
    from . import looks

    looks.sync_looks(scene)
    if settings.aim_mode == "PLACE_DATE":
        from . import place_date

        place_date.evaluate(scene)
    from . import celestials, lamps

    celestials.sync_celestials(scene)
    lamps.sync_lamps(scene)
    return world


def detach(scene: bpy.types.Scene) -> None:
    """Restore previous World, delete OuroSkies World, remove owned lamps, stop handlers."""
    settings = scene.ouroskies
    stop_handlers()

    from . import lamps

    lamps.remove_all_owned_lamps(scene)

    owned = find_ouroskies_world(scene)
    prev_name = settings.previous_world_name
    previous = bpy.data.worlds.get(prev_name) if prev_name else None
    if previous is not None and previous.get(defaults.WORLD_OWNED_KEY):
        previous = None

    if previous is None:
        previous = _fallback_world(exclude=owned)

    if owned is not None and scene.world == owned:
        scene.world = previous
    elif scene.world is None:
        scene.world = previous
    else:
        # Scene already points elsewhere; still prefer restoring remembered World.
        scene.world = previous

    if owned is not None:
        bpy.data.worlds.remove(owned, do_unlink=True)

    settings.previous_world_name = ""
    settings.is_enabled = False


def rebuild(scene: bpy.types.Scene) -> bool:
    """Rebuild canonical sky graph from Scene settings. Returns False if not enabled."""
    settings = scene.ouroskies
    if not settings.is_enabled:
        return False
    world = find_ouroskies_world(scene)
    if world is None:
        return False
    rebuild_sky_graph(world, settings)
    if scene.world != world:
        scene.world = world
    if settings.aim_mode == "PLACE_DATE":
        from . import place_date

        place_date.evaluate(scene)
    from . import celestials, lamps, looks

    looks.sync_looks(scene)
    celestials.sync_celestials(scene)
    lamps.sync_lamps(scene)
    return True


def reset_atmosphere(scene: bpy.types.Scene) -> None:
    settings = scene.ouroskies
    settings.air = defaults.ATMOSPHERE["air"]
    settings.dust = defaults.ATMOSPHERE["dust"]
    settings.ozone = defaults.ATMOSPHERE["ozone"]
    settings.altitude = defaults.ATMOSPHERE["altitude"]
    sync_atmosphere(scene)
