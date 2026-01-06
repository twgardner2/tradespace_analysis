from manim import *
import math
import numpy as np

class FOV(VGroup):
    def __init__(self, origin, cross, angle_deg, **kwargs):
        super().__init__(*kwargs)

        # Calculate downtrack distance for angle and crosstrack distance
        angle_rad = angle_deg * PI/360
        downtrack = (cross/2) / math.tan(angle_rad/2)

        # Create/add polygon
        self.fov = VGroup(
            Polygon(
                origin, origin + downtrack*UP + cross/2*LEFT, origin + downtrack*UP + cross/2*RIGHT,
                stroke_color=YELLOW
            ).set_fill(YELLOW, opacity=0.15)
        )
        self.add(self.fov)



class UAV(VGroup):

    def __init__(self, fov_width: float, fov_deg: float, w_height_det_fov: bool = False, w_beam_det_fov: bool = False, **kwargs):
        super().__init__(**kwargs)

        # Create the UAV as a triangle with a sharper point at the front
        self.uav = Polygon(
            [-0.15, -0.1, 0],  # Bottom left
            [0.15, -0.1, 0],   # Bottom right
            [0, 0.3, 0],       # Top (sharper point)
            color=YELLOW, fill_opacity=1
        ).scale(0.9).move_to(2*DOWN + LEFT * (3/2)*fov_width)

        self.add(self.uav)

        if w_height_det_fov:
            # Create sensor FOV vs. design target's height dimension (shorter detection range)
            self.fov_height = FOV(origin=self.uav.get_top(), cross=fov_width, angle_deg=fov_deg)
            # Group UAV and FOV
            self.add(self.fov_height)

        # Optionally create sensor FOV vs. design target's length dimension (longer detection range)
        if w_beam_det_fov:
            self.fov_beaming = FOV(origin=self.uav.get_top(), cross=1.5*fov_width, angle_deg=fov_deg)
            self.add(self.fov_beaming)



class DesignTarget(VGroup):

    def __init__(self, debug=False, **kwargs):
        super().__init__(**kwargs)

        # Create the target as a triangle
        self.triangle = Polygon(
            [-0.04, -0.04, 0],  # Bottom left
            [-0.04, 0.04, 0],   # Bottom right
            [0.05, 0, 0],       # Top (apex)
            color=RED, fill_opacity=1
        )
        self.add(self.triangle)

        if debug:
            self.bow_dot = Dot(self.triangle.get_top(), color=BLUE)
            self.bow_dot.align_to(self.triangle, UP)
            self.add(self.bow_dot)



class Dimension3D(VGroup):
    def __init__(
        self,
        start,
        end,
        tick_direction,
        # label=None,
        offset=2 * UP,
        tick_radius=0.06,
        color=WHITE,
        # label_buff=0.35,
        **kwargs
    ):
        super().__init__(**kwargs)

        start = np.array(start)
        end = np.array(end)
        offset = np.array(offset)
        tick_direction = normalize(np.array(tick_direction))

        dim_dir = normalize(end - start)

        # ---------------- Dimension line ----------------
        dim_line = Line(
            start + offset,
            end + offset,
            color=color,
            stroke_width=3
        )

        # ---------------- Tick markers (spheres) ----------------
        ticks = VGroup()
        for p in [start + offset, end + offset]:
            tick = Sphere(
                radius=tick_radius,
                resolution=(12, 24),
                fill_opacity=1,
                color=color
            )
            tick.move_to(p)
            ticks.add(tick)

        self.add(dim_line, ticks)

        # # ---------------- Label ----------------
        # if label is not None:
        #     text = Text(label, font_size=36, color=color)

        #     # Align text with dimension direction
        #     if not np.allclose(dim_dir, RIGHT):
        #         axis = np.cross(RIGHT, dim_dir)
        #         angle = np.arccos(np.clip(np.dot(RIGHT, dim_dir), -1, 1))
        #         if np.linalg.norm(axis) > 1e-6:
        #             text.rotate(angle, axis=axis)

        #     # Ensure readability from +X +Y +Z
        #     view_dir = normalize(RIGHT + UP + OUT)
        #     normal = np.cross(dim_dir, tick_direction)

        #     if np.dot(normal, view_dir) < 0:
        #         text.rotate(PI, axis=dim_dir)

        #     text.move_to(
        #         (start + end) / 2
        #         + offset
        #         + label_buff * tick_direction
        #     )

        #     self.add(text)

        self.dim_line = dim_line
        self.ticks = ticks