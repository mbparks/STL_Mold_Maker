import trimesh
import os
import argparse


def create_negative_space_mold(input_file):
    # Load the input STL file
    original_mesh = trimesh.load_mesh(input_file)

    # Ensure the original mesh is watertight
    if not original_mesh.is_watertight:
        raise ValueError("Input mesh must be watertight for mold creation.")

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

    # Step 2: Subtract the object to create the cavity (negative space)
    mold_with_cavity = trimesh.boolean.difference([mold_block, original_mesh])

    # Step 3: Split the mold into top and bottom halves along the middle of the z-axis
    z_split = (min_corner[2] + max_corner[2]) / 2

    # Create a splitting box for the top half
    top_split_box = trimesh.creation.box(
        extents=[mold_block_size[0], mold_block_size[1], mold_block_size[2] / 2],
        transform=trimesh.transformations.translation_matrix(
            [(min_corner[0] + max_corner[0]) / 2,  # Center X
             (min_corner[1] + max_corner[1]) / 2,  # Center Y
             z_split + mold_block_size[2] / 4]  # Top half center
        )
    )

    # Create a splitting box for the bottom half
    bottom_split_box = trimesh.creation.box(
        extents=[mold_block_size[0], mold_block_size[1], mold_block_size[2] / 2],
        transform=trimesh.transformations.translation_matrix(
            [(min_corner[0] + max_corner[0]) / 2,  # Center X
             (min_corner[1] + max_corner[1]) / 2,  # Center Y
             z_split - mold_block_size[2] / 4]  # Bottom half center
        )
    )

    # Split the mold into two halves
    mold_top = trimesh.boolean.intersection([mold_with_cavity, top_split_box])
    mold_bottom = trimesh.boolean.intersection([mold_with_cavity, bottom_split_box])

    # Step 4: Add alignment keys to the cavity face
    key_radius = wall_thickness / 4
    key_height = wall_thickness
    key_positions = [
        [min_corner[0] + wall_thickness, min_corner[1] + wall_thickness, z_split],  # Bottom-left corner
        [max_corner[0] - wall_thickness, min_corner[1] + wall_thickness, z_split],  # Bottom-right corner
        [min_corner[0] + wall_thickness, max_corner[1] - wall_thickness, z_split],  # Top-left corner
        [max_corner[0] - wall_thickness, max_corner[1] - wall_thickness, z_split],  # Top-right corner
    ]

    for position in key_positions:
        # Create a key cylinder
        key = trimesh.creation.cylinder(
            radius=key_radius,
            height=key_height,
            sections=32
        )
        # Position the key on the cavity face
        key.apply_translation([position[0], position[1], position[2]])

        # Add key to the bottom mold
        mold_bottom = trimesh.boolean.union([mold_bottom, key])

        # Subtract the key from the top mold
        mold_top = trimesh.boolean.difference([mold_top, key])

    # Step 5: Add a wax pour spout to the cavity in the top mold
    pour_spout_radius = wall_thickness / 3
    pour_spout_height = wall_thickness * 3
    pour_spout = trimesh.creation.cylinder(
        radius=pour_spout_radius,
        height=pour_spout_height,
        sections=32
    )

    # Position the pour spout to connect with the cavity
    pour_spout_position = [
        (min_corner[0] + max_corner[0]) / 2,  # Center X
        (min_corner[1] + max_corner[1]) / 2,  # Center Y
        z_split + pour_spout_height / 2  # Above the cavity in the top mold
    ]
    pour_spout.apply_translation(pour_spout_position)

    # Subtract the pour spout from the top mold
    mold_top = trimesh.boolean.difference([mold_top, pour_spout])

    # Generate output file names
    base_name = os.path.splitext(os.path.basename(input_file))[0]
    output_top = f"{base_name}_mold_top.stl"
    output_bottom = f"{base_name}_mold_bottom.stl"

    # Save the resulting mold halves
    mold_top.export(output_top)
    mold_bottom.export(output_bottom)

    print(f"Mold halves saved as '{output_top}' and '{output_bottom}'.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Create a negative space mold with interlocking alignment keys and a wax pour spout."
    )
    parser.add_argument("input_file", type=str, help="Path to the input STL file.")

    args = parser.parse_args()

    if not os.path.exists(args.input_file):
        print(f"Input file '{args.input_file}' does not exist.")
    else:
        create_negative_space_mold(args.input_file)
