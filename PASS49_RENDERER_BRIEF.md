# Pass 49 Renderer Brief

The Observatory now has one atmospheric truth path:

`active scene inputs -> Pass 48 governing model -> relative influence grid + model support grid -> Pass 49 renderer`

## Visual grammar
- **Brightness:** run-relative modeled atmospheric influence.
- **Texture:** model support. Texture fragments deterministically as support weakens.

## Retired from the primary Observatory
- Procedural plume lanes and ribbons.
- Random particle placement.
- The separate animated directional breath canvas.

## Projection
The field grid is projected around the selected source with a local downwind/crosswind affine basis computed from the model transport bearing. Transparent cells remain transparent; the computational domain is not displayed as a rectangle.
