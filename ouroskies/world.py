# SPDX-License-Identifier: GPL-3.0-or-later

"""OuroSkies World lifecycle and minimal Multiple Scattering sky graph."""

from __future__ import annotations

import bpy

from . import defaults


def stop_handlers() -> None:
    """Stop per-frame / depsgraph handlers. None registered yet."""


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
    """Author canonical minimal tree: Sky (MS) → Background → World Output."""
    world.use_nodes = True
    node_tree = world.node_tree
    node_tree.nodes.clear()

    sky = node_tree.nodes.new("ShaderNodeTexSky")
    sky.name = defaults.NODE_SKY
    sky.label = defaults.NODE_SKY
    sky.location = (-300.0, 0.0)
    sky.sky_type = "MULTIPLE_SCATTERING"
    apply_atmosphere_to_sky(sky, settings)

    background = node_tree.nodes.new("ShaderNodeBackground")
    background.name = defaults.NODE_BACKGROUND
    background.label = defaults.NODE_BACKGROUND
    background.location = (0.0, 0.0)

    output = node_tree.nodes.new("ShaderNodeOutputWorld")
    output.name = defaults.NODE_OUTPUT
    output.label = defaults.NODE_OUTPUT
    output.location = (300.0, 0.0)

    node_tree.links.new(sky.outputs["Color"], background.inputs["Color"])
    node_tree.links.new(background.outputs["Background"], output.inputs["Surface"])


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
        return existing

    previous = scene.world
    settings.previous_world_name = previous.name if previous is not None else ""

    world = bpy.data.worlds.new(_unique_world_name())
    world[defaults.WORLD_OWNED_KEY] = True
    rebuild_sky_graph(world, settings)
    scene.world = world
    settings.is_enabled = True
    return world


def detach(scene: bpy.types.Scene) -> None:
    """Restore previous World, delete OuroSkies World, stop handlers."""
    settings = scene.ouroskies
    stop_handlers()

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
    return True


def reset_atmosphere(scene: bpy.types.Scene) -> None:
    settings = scene.ouroskies
    settings.air = defaults.ATMOSPHERE["air"]
    settings.dust = defaults.ATMOSPHERE["dust"]
    settings.ozone = defaults.ATMOSPHERE["ozone"]
    settings.altitude = defaults.ATMOSPHERE["altitude"]
    sync_atmosphere(scene)
