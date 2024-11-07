"""
Scan paths and times, written by Joe Knapper

Copyright Joe Knapper 2020, released under GNU GPL v3
"""


import numpy as np 
#import matplotlib.pyplot as plt

def ordered_spiral(starting_x, starting_y, number_of_shells, x_move, y_move):

    # coords_list is the full list of sites to take an image
    coords_list = [(starting_x, starting_y)]

    # current location is the working site, which is always appended to coords_list if it's unique
    current_location = (starting_x, starting_y)

    # a list of the directions the scan will move in
    movements_list = [(x_move, 0), (0, -y_move), (-x_move, 0), (0, y_move)]

    # iterates for each "shell"
    for s in range(2, number_of_shells+1):
        side_length = (2*s)-1
        current_location = tuple(np.add(current_location, (0, y_move)))
        coords_list.append(current_location)

        for direction in movements_list:
            for i in range(1, side_length):
                if direction == tuple((x_move,0)) and i == side_length-1: break
                current_location = tuple(np.add(current_location, direction))
                if current_location not in coords_list: coords_list.append(current_location)
    return(coords_list)

def raster(starting_x,starting_y,x_move,y_move,rows,columns):
    coords_list = []
    current_location = (starting_x, starting_y)
    for x in range(0,columns):
        current_location = tuple((current_location[0], starting_y))
        coords_list.append(current_location)
        for y in range(1,rows):
            current_location = tuple((current_location[0],current_location[1] - y_move))
            coords_list.append(current_location)
        current_location = tuple((current_location[0] + x_move,current_location[1]))
    coords_list.append((starting_x,starting_y))
    return(coords_list)

def snake(starting_x,starting_y,x_move,y_move,rows,columns):
    coords_list = []
    current_location = (starting_x, starting_y)
    for x in range(0,columns):
        coords_list.append(current_location)
        for y in range(1,rows):
            if x % 2 != 0:
                current_location = tuple((current_location[0],current_location[1] + y_move))
            elif x % 2 == 0:
                current_location = tuple((current_location[0],current_location[1] - y_move))
            else: print("issue")
            coords_list.append(current_location)
        current_location = tuple((current_location[0] + x_move,current_location[1]))
    coords_list.append((starting_x,starting_y))
    return(coords_list)

def plot_path(path):
    import matplotlib.pyplot as plt
    x_val = [x[0] for x in path]
    y_val = [x[1] for x in path]
    plt.plot(x_val,y_val)
    plt.plot(x_val,y_val,'or')
    plt.show()


def path_length(points_list):
    running_total = 0
    for point in range(1,len(points_list)):
        displacement = tuple(np.subtract(points_list[point],points_list[point-1]))
        distance = np.max(np.absolute(displacement))
        running_total = running_total + distance
    return(running_total)

# focus type 0 means no autofocus, type 1 means fast autofocus
def time_estimate(points_list,focus_type):
    distance_travelled = path_length(points_list)
    time_travelling = distance_travelled * (1/1000)
    print(time_travelling)
    if focus_type == 0:
        time_capturing = (len(points_list)-1)*1.5
    elif focus_type == 1:
        time_capturing = (len(points_list)-1)*5.5
    else: print("Please use a valid focus type")

    return time_capturing+time_travelling

if __name__ == "__main__":
    plot_path(snake(0,0,640,480,4,5))

    #path = snake(0,0,1000,1000,5,5)
    #print(time_estimate(path,1))
