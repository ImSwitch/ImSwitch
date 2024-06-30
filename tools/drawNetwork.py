import matplotlib.pyplot as plt
import numpy as np
# Use the line function from skimage
from skimage.draw import line

def createBranchingTree(width=5000, height=5000):
    np.random.seed(0)  # Set a random seed for reproducibility
    # Define the dimensions of the image
    width, height = 5000, 5000

    # Create a blank white image
    image = np.ones((height, width), dtype=np.uint8) * 255

    # Function to draw a line (blood vessel) on the image
    def draw_vessel(start, end, image):
        rr, cc = line(start[0], start[1], end[0], end[1])
        try:image[rr, cc] = 0  # Draw a black line
        except:
            end=0
            return

    # Recursive function to draw a tree-like structure
    def draw_tree(start, angle, length, depth, image, reducer, max_angle=40):
        if depth == 0:
            return
        
        # Calculate the end point of the branch
        end = (
            int(start[0] + length * np.sin(np.radians(angle))),
            int(start[1] + length * np.cos(np.radians(angle)))
        )
        
        # Draw the branch
        draw_vessel(start, end, image)
        
        # change the angle slightly to add some randomness
        angle += np.random.uniform(-10, 10)
        
        # Recursively draw the next level of branches
        new_length = length * reducer  # Reduce the length for the next level
        new_depth = depth - 1
        draw_tree(end, angle - max_angle*np.random.uniform(-1, 1), new_length, new_depth, image, reducer)
        draw_tree(end, angle + max_angle*np.random.uniform(-1, 1), new_length, new_depth, image, reducer)

    # Starting point and parameters
    start_point = (height - 1, width // 2)
    initial_angle = -90  # Start by pointing upwards
    initial_length = np.max((width, height))*.15  # Length of the first branch
    depth = 7  # Number of branching levels
    reducer = .9
    # Draw the tree structure
    draw_tree(start_point, initial_angle, initial_length, depth, image, reducer)
    return image

if __name__ == "__main__":
    image = createBranchingTree(width=5000, height=5000)
    # Display the image
    plt.imshow(image, cmap='gray')
    plt.axis('off')  # Hide the axis
    plt.show()
