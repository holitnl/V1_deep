import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import RectangleSelector, Button

# Function to parse G-code file and extract relevant data
def parse_gcode(file_path):
    """
    Parses a G-code file and extracts X, Y, and extrusion values.
    
    :param file_path: Path to the G-code file.
    :return: Numpy array of shape (N, 3) representing [x, y, extrusion] values.
    """
    gcode_data = []
    with open(file_path, 'r') as file:
        for line in file:
            if 'G1' in line:  # Only process G1 commands (movement with extrusion)
                parts = line.strip().split()
                x, y, e = None, None, None
                for part in parts:
                    if part.startswith('X'):
                        x = float(part[1:])
                    elif part.startswith('Y'):
                        y = float(part[1:])
                    elif part.startswith('E'):
                        e = float(part[1:])
                if x is not None and y is not None and e is not None:
                    gcode_data.append([x, y, e])
    return np.array(gcode_data)

# Function to write modified G-code back to a file
def write_gcode(file_path, gcode_data, original_file_path):
    """
    Writes modified G-code data back to a file.
    
    :param file_path: Path to save the modified G-code.
    :param gcode_data: Numpy array of shape (N, 3) representing [x, y, extrusion] values.
    :param original_file_path: Path to the original G-code file to copy non-G1 commands.
    """
    with open(original_file_path, 'r') as original_file, open(file_path, 'w') as output_file:
        gcode_index = 0
        for line in original_file:
            if 'G1' in line:
                # Replace extrusion value in G1 commands
                parts = line.strip().split()
                new_line = []
                for part in parts:
                    if part.startswith('E'):
                        if gcode_index < len(gcode_data):  # Ensure index is within bounds
                            new_line.append(f'E{gcode_data[gcode_index, 2]:.5f}')
                            gcode_index += 1
                        else:
                            new_line.append(part)  # Keep original value if index is out of bounds
                    else:
                        new_line.append(part)
                output_file.write(' '.join(new_line) + '\n')
            else:
                # Copy non-G1 commands as-is
                output_file.write(line)

# Function to adjust extrusion values instantly within a selected area
def adjust_extrusion(gcode, x_range, y_range, target_ratio):
    """
    Adjusts the extrusion values instantly within the specified area.
    
    :param gcode: Numpy array of shape (N, 3) representing the G-code data.
    :param x_range: Tuple (x_min, x_max) defining the x-range of the selected area.
    :param y_range: Tuple (y_min, y_max) defining the y-range of the selected area.
    :param target_ratio: The target extrusion ratio to apply.
    :return: Modified G-code data with adjusted extrusion values.
    """
    x_min, x_max = x_range
    y_min, y_max = y_range
    
    # Debugging: Print the ranges and target ratio
    print(f"Adjusting extrusion for x_range={x_range}, y_range={y_range}, target_ratio={target_ratio}")
    
    # Create a mask for points within the selected area
    mask = (gcode[:, 0] >= x_min) & (gcode[:, 0] <= x_max) & (gcode[:, 1] >= y_min) & (gcode[:, 1] <= y_max)
    
    # Adjust extrusion values instantly
    gcode[mask, 2] *= target_ratio
    
    # Debugging: Print the modified extrusion values
    print(f"Modified extrusion values: {gcode[mask, 2]}")
    
    return gcode

# Global variables to store selected areas and multipliers
selected_areas = []
extrusion_multipliers = []

# Function to handle rectangle selection
def on_select(eclick, erelease):
    """
    Handles the selection of a rectangle on the plot.
    
    :param eclick: The click event.
    :param erelease: The release event.
    """
    global x_range, y_range
    x1, y1 = eclick.xdata, eclick.ydata
    x2, y2 = erelease.xdata, erelease.ydata
    x_range = (min(x1, x2), max(x1, x2))
    y_range = (min(y1, y2), max(y1, y2))
    
    print(f"Rectangle selected: x_range={x_range}, y_range={y_range}")
    
    # Enable the confirm button after selection
    confirm_button.set_active(True)

# Function to confirm selection and apply extrusion multiplier
def confirm_selection(event):
    """
    Confirms the selection and applies the extrusion multiplier.
    """
    global gcode_data, selected_areas, extrusion_multipliers, x_range, y_range
    
    print("Confirm button clicked!")
    
    # Disable the confirm button after confirmation
    confirm_button.set_active(False)
    
    # Use a modal dialog to input the extrusion multiplier
    target_ratio = input("Enter the extrusion multiplier (e.g., 1.5 for 50% increase): ")
    
    try:
        target_ratio = float(target_ratio)
        print(f"Extrusion multiplier entered: {target_ratio}")
        
        # Add the selected area and multiplier to the lists
        selected_areas.append((x_range, y_range))
        extrusion_multipliers.append(target_ratio)
        
        # Adjust extrusion values for the selected area
        gcode_data = adjust_extrusion(gcode_data, x_range, y_range, target_ratio)
        
        # Update the plot with downsampled data for better performance
        ax.clear()
        downsampled_data = gcode_data[::10]  # Downsample for faster visualization
        ax.scatter(downsampled_data[:, 0], downsampled_data[:, 1], c=downsampled_data[:, 2], cmap='viridis', s=1)
        
        # Draw rectangles for selected areas
        for (x_range_, y_range_), multiplier in zip(selected_areas, extrusion_multipliers):
            width = x_range_[1] - x_range_[0]
            height = y_range_[1] - y_range_[0]
            rect = plt.Rectangle((x_range_[0], y_range_[0]), width, height, edgecolor='red', facecolor='none')
            ax.add_patch(rect)
            ax.text(x_range_[0], y_range_[1], f'x{multiplier:.2f}', color='red', fontsize=8)
        
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.set_title('G-code Visualization with Instant Extrusion Adjustment')
        plt.draw()
    except ValueError:
        print("Invalid input. Please enter a valid number.")
    except Exception as e:
        print(f"An error occurred: {e}")

# Main script
if __name__ == "__main__":
    # Parse the input G-code file
    input_file = 'input.gcode'
    gcode_data = parse_gcode(input_file)
    
    # Debugging: Print the shape of gcode_data
    print(f"G-code data shape: {gcode_data.shape}")
    
    # Downsample data for visualization
    downsampled_data = gcode_data[::10]  # Only plot every 10th point
    
    # Visualization setup
    fig, ax = plt.subplots()
    ax.scatter(downsampled_data[:, 0], downsampled_data[:, 1], c=downsampled_data[:, 2], cmap='viridis', s=1)
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_title('G-code Visualization with Instant Extrusion Adjustment')
    
    # Rectangle selector for area selection
    rs = RectangleSelector(ax, on_select, useblit=True, button=[1], minspanx=5, minspany=5, spancoords='pixels', interactive=True)
    
    # Confirm button for selection
    confirm_ax = plt.axes([0.7, 0.9, 0.2, 0.05])  # Position the confirm button at the top
    confirm_button = Button(confirm_ax, 'Confirm Selection')
    confirm_button.on_clicked(confirm_selection)
    confirm_button.set_active(False)  # Disable button initially
    
    plt.show()
    
    # Save the modified G-code to output.gcode
    output_file = 'output.gcode'
    write_gcode(output_file, gcode_data, input_file)
    print(f"Modified G-code saved to {output_file}")