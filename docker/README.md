# Dockerfile for ImSwitch

Inspired by https://github.com/napari/napari/blob/main/dockerfile

## Build 

Open a terminal or command prompt and navigate to the directory containing the Dockerfile. Use the `docker build` command to build your Docker image. You'll need to tag your image with a name for easy reference. For example:

```bash
cd ./docker
docker build -t imswitch-image . # sudo on Linux
```

Here, `imswitch-image` is the tag name for the Docker image, and the `.` at the end of the command denotes the current directory where the Dockerfile is located.


## Run 

Once the image is built, you can run a container based on this image. Use the `docker run` command for this:

   ```bash
   docker run -d --name imswitch-container imswitch-image
   docker run -d --name imswitch-container --platform linux/amd64 imswitch-image
    docker run -d --name imswitch-container --platform darwin/arm64 imswitch-image
   ```

This command will start a new container named `imswitch-container` in detached mode (the `-d` flag), which means the container runs in the background. If your application requires interaction or you need to see its output directly, you can omit the `-d` flag.

## Accessing the Container (if needed)

If you need to access the container's terminal, use the `docker exec` command:

```bash
docker exec -it imswitch-container /bin/bash
```

This will open a bash shell inside the container.

## Stopping and Removing the Container

When you're done, you can stop and remove the container using the following commands:

```bash
docker stop imswitch-container
docker rm imswitch-container
```

## Notes on Hardware Access

If your application needs access to specific hardware resources like a camera or USB device, you'll need to add specific flags to the `docker run` command to grant that access. For instance:

**TODO:** How can we access the Daheng camera?

```bash
docker run -d --name imswitch-container \
    --device /dev/video0:/dev/video0 \
    --device /dev/ttyUSB0:/dev/ttyUSB0 \
    imswitch-image
```

Adjust the device paths (`/dev/video0`, `/dev/ttyUSB0`) according to your system's configuration.

