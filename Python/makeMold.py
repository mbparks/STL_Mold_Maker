import trimesh
import os
import argparse


def create_pour_spout(mold_with_cavity, wall_thickness, min_corner, max_corner, z_split):
    """
    Create a functional pour spout that enters along the x-z face,
    intersects the cavity, and resides entirely in one mold half.
    """
    spout_radius = 2.5  # Max diameter is 5mm
    spout_length = (max_corner[0] - min_corner[0]) * 0.4  # Dynamic length to reach cavity

    # Create the cylindrical spout geometry
    pour_spout = trimesh.creation.cylinder(
        radius=spout_radius,
        height=spout_length,
        sections=32
    )

    # Dynamically position the spout to intersect with the cavity
    spout_position = [
        min_corner[0] + wall_thickness,  # Enter along x-axis (exterior hole)
        (min_corner[1] + max_corner[1]) / 2,  # Center along y-axis
        z_split - wall_thickness  # Align below the cavity to stay in bottom mold
    ]
    pour_spout.apply_translation([
        spout_position[0] + spout_length / 2,  # Center spout length inside mold
        spout_position[1],
        spout_position[2]
    ])

    # Ensure the spout intersects the cavity
    cavity_intersection = trimesh.boolean.intersection([pour_spout, mold_with_cavity])
    if cavity_intersection.is_empty:
        raise ValueError("Pour spout does not intersect with the cavity!")

    return pour_spout


def create_negative_space_mold(input_file):
    # Load the input STL file
    original_mesh = trimesh.load_mesh(input_file)

    # Ensure the original mesh is watertight
    if not original_mesh.is_watertight:
        original_mesh = trimesh.repair.fill_holes(original_mesh)

    # Step 1: Create the outer mold block
    wall_thickness = 10.0  # Ensure at least 10mm wall thickness
    bounding_box = original_mesh.bounds
    min_corner = bounding_box[0] - wall_thickness
    max_corner = bounding_box[1] + wall_thickness

    # Create a mold block enclosing the original object
    mold_block_size = max_corner - min_corner
    mold_block_transform = trimesh.transformations.translation_matrix(
        (min_corner + max_corner) / 2
    )
    mold_block = trimesh.creation.box(
        extents=mold_block_size,
        transform=mold_block_transform
    )

    # Subtract the object to create the cavity
    mold_with_cavity = trimesh.boolean.difference([mold_block, original_mesh])

    # Step 2: Split the mold into top and bottom halves
    z_split = (min_corner[2] + max_corner[2]) / 2

    top_split_box = trimesh.creation.box(
        extents=[mold_block_size[0], mold_block_size[1], mold_block_size[2] / 2],
        transform=trimesh.transformations.translation_matrix(
            [(min_corner[0] + max_corner[0]) / 2,
             (min_corner[1] + max_corner[1]) / 2,
             z_split + mold_block_size[2] / 4]
        )
    )

    bottom_split_box = trimesh.creation.box(
        extents=[mold_block_size[0], mold_block_size[1], mold_block_size[2] / 2],
        transform=trimesh.transformations.translation_matrix(
            [(min_corner[0] + max_corner[0]) / 2,
             (min_corner[1] + max_corner[1]) / 2,
             z_split - mold_block_size[2] / 4]
        )
    )

    mold_top = trimesh.boolean.intersection([mold_with_cavity, top_split_box])
    mold_bottom = trimesh.boolean.intersection([mold_with_cavity, bottom_split_box])

    # Step 3: Add alignment keys
    key_radius = wall_thickness / 4
    key_height = wall_thickness
    key_positions = [
        [min_corner[0] + wall_thickness, min_corner[1] + wall_thickness, z_split],
        [max_corner[0] - wall_thickness, min_corner[1] + wall_thickness, z_split],
        [min_corner[0] + wall_thickness, max_corner[1] - wall_thickness, z_split],
        [max_corner[0] - wall_thickness, max_corner[1] - wall_thickness, z_split],
    ]

    for position in key_positions:
        key = trimesh.creation.cylinder(radius=key_radius, height=key_height, sections=32)
        key.apply_translation([position[0], position[1], position[2]])

        mold_bottom = trimesh.boolean.union([mold_bottom, key])
        mold_top = trimesh.boolean.difference([mold_top, key])

    # Step 4: Create and subtract the pour spout
    pour_spout = create_pour_spout(
        mold_with_cavity, wall_thickness, min_corner, max_corner, z_split
    )
    mold_bottom = trimesh.boolean.difference([mold_bottom, pour_spout])

    # Step 5: Export the molds
    base_name = os.path.splitext(os.path.basename(input_file))[0]
    output_top = f"{base_name}_mold_top.stl"
    output_bottom = f"{base_name}_mold_bottom.stl"

    mold_top.export(output_top)
    mold_bottom.export(output_bottom)

    print(f"Mold halves saved as '{output_top}' and '{output_bottom}'.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Create a negative space mold with a functional pour spout in one mold half."
    )
    parser.add_argument("input_file", type=str, help="Path to the input STL file.")

    args = parser.parse_args()

    if not os.path.exists(args.input_file):
        print(f"Input file '{args.input_file}' does not exist.")
    else:
        create_negative_space_mold(args.input_file)
