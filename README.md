# Blender64
Export mesh from Blender 3D to a n64 display list format. I was interested in N64 homebrew dev for a while and wrote this back around 2014, many things including code style and features could be improved and I pla to revisit this soon hopefully.

![Demo](demo/demo.gif?raw=true "Demo")

It's pretty wonky and embarrassing looking at the code today but the concept is there to build on.

# Features
- Was only tested for Blender v2.76b
- Uses F3DEX2 microcode
- Supports smooth normals based on how I filled up the vertex buffer
- Seems to handle around 2k polygons just fine
- `demo` folder contains 2 roms exported using dev kit and 2 header files containing the model data for the Blender suzanne monkey (one with "hello").

# Next steps
- Want to figure out a better toolchain then a windows 2000 vm
- Get a dev cart and run roms with correct cic/checksum
- Get a better understanding of graphics pipeline and capabilities
- Rewrite everything...
- Refactor as an actual Blender plugin with options for model name, things to include and compression
- Want to support: UV's, materials, textures, vertex colours, possibly rigging and animations