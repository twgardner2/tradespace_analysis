# Generate videos from scenes:
# manim ./manim/scenes.py --config_file ./manim/manim.cfg

# Convert medium quality .mp4 to .gif
# ffmpeg -i SceneName.mp4 -vf "fps=30,scale=720:-1:flags=lanczos,palettegen" palette.png
# ffmpeg -i SceneName.mp4 -i palette.png -filter_complex "fps=30,scale=720:-1:flags=lanczos[x];[x][1:v]paletteuse" output.gif

# manim -pql --disable_caching --fps 5 ./visuals.py Warship3D

from manim import *
import math
import numpy as np
from scene_helpers import (
    Dimension3D,
    FOV,
    UAV,
    DesignTarget,
    MyWarship
)

TEXT_WRITE_TIME = 1 # seconds

class BaseScene(Scene):
    def setup(self):
        # config.frame_height = 6
        # config.frame_width = 8

        WIDTH = 4
        HEIGHT = 4
        self.N_LANES = 4

        # self.add(NumberPlane(
        #     background_line_style={
        #         "stroke_color": TEAL,
        #         "stroke_width": 4,
        #         "stroke_opacity": 0.2
        #     }
        # ))

        # Create the box representing the search area
        search_area = Rectangle(width=WIDTH, height=HEIGHT, color=BLUE).shift(DOWN * 1)
        self.search_area = search_area
        # self.play(Create(search_area))
        self.add(self.search_area)


        # Create lanes in the search area
        lane_width = search_area.width / self.N_LANES
        self.lane_width = lane_width

        lane_boundaries = VGroup()
        for i in range(1, self.N_LANES):
            lane_x = search_area.get_left()[0] + lane_width * i
            boundary = Line(
                start=search_area.get_bottom() + RIGHT * lane_x,
                end=search_area.get_top() + RIGHT * lane_x,
                color=BLUE,
                stroke_width=1,
                # stroke_opacity=0.5
            )
            lane_boundaries.add(boundary)

        # Add dotted flight paths in the center of each lane
        flight_paths = VGroup()
        for lane in lane_boundaries:
            flight_path = DashedLine(
                start=lane.get_start() + 0.5*LEFT,
                end=lane.get_end() + 0.5*LEFT,
                color=WHITE,
                dash_length=0.2
            )
            flight_paths.add(flight_path)
        flight_paths.add(
            DashedLine(
                start=flight_paths[-1].get_start() + lane_width*RIGHT,
                end=flight_paths[-1].get_end() + lane_width*RIGHT,
                color=WHITE,
                dash_length=0.2
            )
        )
        # Add lanes and flight paths to the scene
        self.add(lane_boundaries, flight_paths)


class a_LawnMower(BaseScene):
    def construct(self):

        # Add some targets to the scene
        ## Target 1
        tgt1 = DesignTarget()
        tgt1.move_to(0.8*DOWN + 1.3*RIGHT)
        tgt1_heading = 3/4*PI
        tgt1.rotate(tgt1_heading)
        self.add(tgt1)
        # Define the target's continuous movement animation in the direction it is pointing
        tgt1_continuous_animation = always_redraw(
            lambda: tgt1.shift(0.005 * np.array([math.cos(tgt1_heading), math.sin(tgt1_heading), 0]))
        )
        self.add(tgt1_continuous_animation)
        ## Target 2
        tgt2 = DesignTarget()
        tgt2.move_to(1.3*DOWN + 0.7*LEFT)
        tgt2_heading = PI + 3/7*PI
        tgt2.rotate(tgt2_heading)
        self.add(tgt2)
        # Define the target's continuous movement animation in the direction it is pointing
        tgt2_continuous_animation = always_redraw(
            lambda: tgt2.shift(0.005 * np.array([math.cos(tgt2_heading), math.sin(tgt2_heading), 0]))
        )
        self.add(tgt2_continuous_animation)

        # Add UAV and FOV to the scene
        uav_group = UAV(fov_width=self.lane_width, fov_deg = 35,  w_height_det_fov = False, w_beam_det_fov=False)
        uav_group.scale(0.9).move_to(2*DOWN + LEFT * (3/2)*uav_group.fov_width)
        self.add(uav_group)

        end_first_leg              = 1.5*LEFT  + 1*UP + (uav_group.get_top() - uav_group.get_center())*DOWN
        end_first_leg_turn_point   = 1  *LEFT  + 1*UP 
        end_second_leg             = 0.5*LEFT  + 3*DOWN + (uav_group.get_top() - uav_group.get_center())*UP
        end_second_leg_turn_point  = 0  *LEFT  + 3*DOWN 
        end_third_leg              = 0.5*RIGHT + 1*UP + (uav_group.get_top() - uav_group.get_center())*DOWN
        end_third_leg_turn_point   = 1  *RIGHT + 1*UP 
        end_fourth_leg             = 1.5*RIGHT + 3*DOWN + (uav_group.get_top() - uav_group.get_center())*UP


        # Combine UAV animations
        self.play(
            Succession(
                ApplyMethod(uav_group.move_to, end_first_leg, rate_func=linear),
                Rotate(
                    uav_group, 
                    angle=-PI, 
                    about_point=end_first_leg_turn_point,
                    rate_func=linear
                ),
                ApplyMethod(uav_group.move_to, end_second_leg, rate_func=linear),
                Rotate(
                    uav_group, 
                    angle=PI, 
                    about_point=end_second_leg_turn_point,
                    rate_func=linear
                ),
                ApplyMethod(uav_group.move_to, end_third_leg, rate_func=linear),
                Rotate(
                    uav_group, 
                    angle=-PI, 
                    about_point=end_third_leg_turn_point,
                    rate_func=linear
                ),
                ApplyMethod(uav_group.move_to, end_fourth_leg, rate_func=linear),
            )
        )

        self.wait()




class b_DesignTargetIntro(ThreeDScene):
    def construct(self):

        self.renderer.camera.frame_rate = 6

        # Axes
        axes = ThreeDAxes(
            x_range=(-5, 5, 1),
            y_range=(-5, 5, 1),
            z_range=(-3, 3, 1),
            x_length=18,
            y_length=15,
            z_length=5
        )
        axes.x_axis.set_color(BLUE)
        axes.y_axis.set_color(RED)
        axes.z_axis.set_color(GREEN)
        axes.set_opacity(0.3)

        # Ship
        ship = MyWarship()
        for part in ship:
            part.set_shade_in_3d(False)

        # Dimension indicators
        length_dim = Dimension3D(
            start=ship.hull.get_critical_point(-X_AXIS),
            end=ship.hull.get_critical_point(X_AXIS),
            tick_direction=OUT,
            offset=2.0 * OUT,
        )
        length_dim_label = Text(f'{ship.LENGTH_M} m', font_size=36, color=WHITE)
        length_dim_label.move_to(2.5 * OUT + 1.5*RIGHT)
        self.add_fixed_orientation_mobjects(length_dim_label)
        self.remove(length_dim_label)

        height_dim = Dimension3D(
            start=ship.hull.get_critical_point(-Z_AXIS),
            end=ship.hull.get_critical_point(Z_AXIS) + ship.SUPERSTRUCTURE_DIM[2]*OUT + ship.MAST_HEIGHT*OUT,
            tick_direction=LEFT,
            offset=6.4 *RIGHT,
        )
        height_dim_label = Text(f'{ship.HEIGHT_M:0.0f} m', font_size=36, color=WHITE)
        height_dim_label.move_to(7.4 * RIGHT + (ship.SUPERSTRUCTURE_DIM[2] + ship.MAST_HEIGHT)/2*OUT)
        self.add_fixed_orientation_mobjects(height_dim_label)
        self.remove(height_dim_label)

        width_dim = Dimension3D(
            start=ship.hull.get_critical_point(-Y_AXIS),
            end=ship.hull.get_critical_point(Y_AXIS),
            tick_direction = LEFT,
            offset= 6.4 * LEFT + ship.HULL_DIM[2]/2*OUT,
        )
        width_dim_label = Text(f'{ship.BEAM_M:0.0f} m', font_size=36, color=WHITE)
        width_dim_label.move_to(7.4 * LEFT + ship.HULL_DIM[2]/2*OUT)
        self.add_fixed_orientation_mobjects(width_dim_label)
        self.remove(width_dim_label)

        self.add(axes, ship)

        # Camera positioning
        self.set_camera_orientation(
            phi   = 60 * DEGREES,
            theta = 30 * DEGREES,
            zoom  = 0.3
        )

        self.play(
            FadeIn(length_dim),
            FadeIn(length_dim_label),
            FadeIn(height_dim),
            FadeIn(height_dim_label),
            FadeIn(width_dim),
            FadeIn(width_dim_label),
            run_time=1
        )

        # Zoom in and pan length
        self.move_camera(
            phi      = 80 * DEGREES,
            theta    = 115 * DEGREES,
            zoom     = 0.8,
            run_time = 2
        )
        self.move_camera(
            phi      = 90 * DEGREES,
            theta    = 75 * DEGREES,
            zoom     = 0.8,
            run_time = 2.5
        )

        # Swing over top
        self.move_camera(
            phi      = 10 * DEGREES,
            theta    = 90 * DEGREES,
            zoom     = 0.8,
            run_time = 1.5
        )

        # Show beam
        self.move_camera(
            phi      = 80 * DEGREES,
            theta    = -15 * DEGREES,
            zoom     = 0.8,
            run_time = 2
        )

        # self.move_camera(
        #     phi      = 90 * DEGREES,
        #     theta    = 15 * DEGREES,
        #     zoom     = 0.8,
        #     run_time = 2.5
        # )

        self.move_camera(
            phi      = 60 * DEGREES,
            theta    = 30 * DEGREES,
            zoom     = 0.3,
            run_time = 1
        )

        self.wait(1)




class c_DetectionRanges(Scene):

    def construct(self):

        TGT_LENGTH = 160 #m
        TGT_HEIGHT =  40 #m
        RES = 480
        JOHNSON = 8
        FOV = 60 * 2 * PI /360

        MAX_DET_RNG = (160*RES)/(JOHNSON*FOV)
        SCALE_FACTOR = 6/MAX_DET_RNG

        def world_to_bow_angle_deg(world_deg):
            """
            World: 0° = +X, CCW positive
            Bow:   0° = forward (world 270°), CW positive
            """
            return (world_deg - 270) % 360
        
        def bow_angle_to_label(bow_deg):
            """
            Convert bow-relative angle (0–360)
            to 'Port X', 'Starboard X', '0', or '180'
            """

            bow_deg = bow_deg % 360

            # Straight ahead / astern
            if bow_deg == 0:
                return "0"
            if bow_deg == 180:
                return "180"

            # Starboard side (0 < angle < 180)
            if bow_deg < 180:
                return f"Starboard {int(round(bow_deg))}"

            # Port side (180 < angle < 360)
            return f"Port {int(round(360 - bow_deg))}"

        def world_angle_to_bow_label(world_angle):
            # ValueTracker is animated in radians; convert to world-degrees for labeling.
            world_deg = (world_angle * 180 / PI) % 360
            bow_deg = world_to_bow_angle_deg(world_deg)
            return bow_angle_to_label(bow_deg)

        def tgt_length_cross_track():
            current_tgt_aob = tgt_aob.get_value()
            tgt_x =  abs(TGT_LENGTH*math.cos(current_tgt_aob))
            return tgt_x

        tgt_aob = ValueTracker(0)
        tgt_aob_label = always_redraw(
            lambda: VGroup(
            Text(
                "AOB:",
                font_size=28,
                color=WHITE,
            ),
            Text(
                world_angle_to_bow_label(tgt_aob.get_value()),
                font_size=28,
                color=WHITE,
            ),
            Text(
                "Length Cross-Track:",
                font_size=28,
                color=WHITE,
            ),
            Text(
                f'{tgt_length_cross_track():0.0f} m',
                font_size=28,
                color=WHITE,
            ),
            Text(
                "Height:",
                font_size=28,
                color=WHITE,
            ),
            Text(
                '40 m',
                font_size=28,
                color=WHITE,
            ),
            )
            # Left-align the two lines with each other so the second line doesn't
            # re-center as its text length changes.
            .arrange(DOWN, aligned_edge=LEFT, buff=0.15)
            # Anchor the whole label block to a fixed point on screen.
            .move_to(6 * LEFT + 2 * UP, aligned_edge=LEFT)
        )
        self.add(tgt_aob_label)

        
        # Simple top-down ship deck silhouette (facing RIGHT, pointed bow, flat stern)
        tgt_pts = [
            # Center ship on y-axis: midpoint between bow tip (max x) and stern (min x) at x=0.
            # Bow tip x =  2.0, stern x = -1.6  -> midpoint = (2.0 + (-1.6)) / 2 = 0.2
            (2.0 - 0.2) * RIGHT + 0.0 * UP,    # Bow tip
            (1.4 - 0.2) * RIGHT + 0.35 * UP,   # Upper bow shoulder
            (0.8 - 0.2) * RIGHT + 0.35 * UP,   # Upper mid
            (-1.6 - 0.2) * RIGHT + 0.35 * UP,  # Upper stern corner
            (-1.6 - 0.2) * RIGHT + 0.0 * UP,   # Stern center (flat)
            (-1.6 - 0.2) * RIGHT - 0.35 * UP,  # Lower stern corner
            (0.8 - 0.2) * RIGHT - 0.35 * UP,   # Lower mid
            (1.4 - 0.2) * RIGHT - 0.35 * UP,   # Lower bow shoulder
        ]
        tgt = Polygon(
            *tgt_pts,
            stroke_color=WHITE,
            stroke_width=3,
        ).set_fill(
            color=GRAY, opacity=0.35
        ).scale(0.3).shift(3 * UP)
        self.add(tgt)
        
        def det_rng():
            current_tgt_aob = tgt_aob.get_value()
            tgt_x =  max(TGT_HEIGHT, abs(TGT_LENGTH*math.cos(current_tgt_aob)))
            return (tgt_x*RES)/(JOHNSON*FOV)

        def downtrack_dist():
            # return det_rng() * math.cos(FOV/2) * SCALE_FACTOR
            return det_rng() * SCALE_FACTOR
        
        def cross_dist():
            return det_rng() * math.tan(FOV/2) * SCALE_FACTOR



        # Labels ----------
        # det_rng_label = always_redraw(
        #     lambda: Text(
        #         f"Detection Range: {det_rng():0.0f} m",
        #         font_size=28,
        #         color=WHITE,
        #     ).shift(4 * LEFT + 1 * UP)
        # )
        # det_rng_label.shift(3*LEFT)
        # def update_det_rng_label(m):
        #     m.set_value(det_rng())
        # det_rng_label.add_updater(update_det_rng_label)
        # self.add(det_rng_label)

        uav = UAV(fov_width=1, fov_deg=25, w_height_det_fov=False, w_beam_det_fov=False)
        uav.shift(3 * DOWN)
        self.add(uav)

        # Anchor the cone to the UAV "nose" (frontmost point) and keep a constant visual offset
        # from the UAV center to that nose; do not scale this by SCALE_FACTOR (that's for range geometry).
        def uav_nose():
            return uav.get_critical_point(Y_AXIS)

        nose_offset = uav_nose() - uav.get_center()

        fov_cone = Polygon(
                uav_nose(),
                uav_nose() + downtrack_dist() * UP + cross_dist() / 2 * LEFT,
                uav_nose() + downtrack_dist() * UP + cross_dist() / 2 * RIGHT,
                stroke_color=YELLOW
            ).set_fill(YELLOW, opacity=0.15)

        # Keep the cone attached to the UAV nose and update as the UAV moves/rotates.
        fov_cone.add_updater(
            lambda m: m.become(
                Polygon(
                    uav.get_center() + nose_offset,
                    uav.get_center() + nose_offset
                    + downtrack_dist() * UP
                    + (cross_dist() / 2) * LEFT,
                    uav.get_center() + nose_offset
                    + downtrack_dist() * UP
                    + (cross_dist() / 2) * RIGHT,
                    stroke_color=YELLOW,
                ).set_fill(YELLOW, opacity=0.15)
            )
        )
        self.add(fov_cone)

        # Make target continuously match the current tgt_aob
        tgt_aob_ref = ValueTracker(0)

        def update_tgt_rotation(m):
            # Rotate by the delta since last frame (avoids compounding / set_angle issues)
            new_aob = tgt_aob.get_value()
            delta = new_aob - tgt_aob_ref.get_value()
            m.rotate(delta)
            tgt_aob_ref.set_value(new_aob)

        tgt.add_updater(update_tgt_rotation)
        self.add(tgt)

        # Updater: shift the UAV vertically based on detection range
        # Starts at the lowest position (3*DOWN). As det_rng decreases, move up by SCALE_FACTOR * det_rng.
        base_uav_pos = uav.get_center()

        def update_uav_pos(m):
            y_offset = SCALE_FACTOR * (MAX_DET_RNG-det_rng())
            m.move_to(base_uav_pos + y_offset * UP)

        uav.add_updater(update_uav_pos)

        self.play(tgt_aob.animate.set_value(2*PI), run_time=8, rate_func=linear)
        # self.play(tgt_aob.animate.set_value(PI), run_time=8, rate_func=linear)
        self.wait(2)

class SensorGapWhenTurning(BaseScene):
    def construct(self):


        # Add UAV and FOV to the scene
        uav_group = UAV(fov_width=self.lane_width, fov_deg = 35,  w_height_det_fov = True, w_beam_det_fov=False)
        uav_group.scale(0.9).move_to(2*DOWN + LEFT * (3/2)*uav_group.fov_width)
        self.add(uav_group)

        dist_top_uav_to_center_group = uav_group.get_center() - uav_group.uav.get_top() 
        start_first_leg     = ((2+dist_top_uav_to_center_group)*DOWN + 1.5*LEFT   )
        end_first_leg       = ( (1+dist_top_uav_to_center_group)*UP + 1.5*LEFT)
        turn_rotation_point = ( 1*UP + 1*LEFT            )
        end_second_leg      = ((3+dist_top_uav_to_center_group)*DOWN + 1.5*RIGHT) 

        # turn_rot_point_dot = Dot(point=turn_rotation_point, color=RED)
        # self.add(turn_rot_point_dot)

        self.play(
            Succession(
                # 1. Shift upwards
                ApplyMethod(uav_group.move_to, end_first_leg, rate_func=linear),
                
                # 2. Rotate
                Rotate(
                    uav_group, 
                    angle=-PI, 
                    about_point=turn_rotation_point,
                    rate_func=linear
                ),
            )
        )

        # Draw sensor gap
        not_covered_gap = Polygon(
            uav_group.uav.get_bottom(), 
            uav_group.uav.get_bottom() + LEFT*self.lane_width/2, 
            uav_group.uav.get_bottom() + LEFT*self.lane_width/2 + (uav_group.uav.get_bottom()-uav_group.fov_height.get_bottom())*DOWN,
            stroke_width=0.5
        ).set_fill(WHITE, opacity=0.3)
        not_covered_level_gap = Polygon(
            uav_group.uav.get_bottom(), 
            uav_group.uav.get_bottom() + RIGHT*self.lane_width/2, 
            uav_group.uav.get_bottom() + RIGHT*self.lane_width/2 + (uav_group.uav.get_bottom()-uav_group.fov_height.get_bottom())*DOWN,
            stroke_width=0.5
        ).set_fill(WHITE, opacity=0.3)
        self.play(FadeIn(not_covered_gap), FadeIn(not_covered_level_gap))

        not_covered_text = Text('Not Covered', color=BLUE, font_size=20).next_to(self.search_area, UP).shift(2*LEFT + 0.15*UP)
        not_covered_arrow = Arrow(not_covered_text.get_bottom(), not_covered_gap.get_center(), color=BLUE)

        not_covered_level_text = Paragraph(
            'Not Covered', 'Straight & Level', color=BLUE, font_size=20, alignment='center'
        ).next_to(self.search_area, UP).shift(1*RIGHT)
        not_covered_level_arrow = Arrow(not_covered_level_text.get_bottom(), not_covered_level_gap.get_center(), color=BLUE)

        self.play(Write(not_covered_text), Write(not_covered_arrow), Write(not_covered_level_text), Write(not_covered_level_arrow), run_time=TEXT_WRITE_TIME)

        # End the animation
        self.wait(10)



class ShortLateralOffsetTurn(BaseScene):
    def construct(self):

        # Add UAV and it's FOV
        uav_group = UAV(fov_width=self.lane_width, fov_deg=35)
        uav_group.scale(0.9).move_to(1*UP + (uav_group.uav.get_top()-uav_group.uav.get_center())*DOWN + LEFT * (3/2)*uav_group.fov_width)
        self.add(uav_group)

        # Calculations for S < 2R turn
        s = 1
        r = ValueTracker(0.6)

        def get_dist():
            current_r = r.get_value()
            c = 2*current_r
            a = current_r + s/2
            b2 = max(0, c**2 - a**2)
            return b2**0.5
        
        def get_theta1():
            current_r = r.get_value()
            return math.acos(  (current_r + s/2   ) / ( 2*current_r  )   )
        
        def get_theta2():
            return math.pi + 2*get_theta1()


        lane_boundary = ( 1*UP + 1*LEFT            )
        # dist_top_uav_to_center_group = uav_group.get_center() - uav.get_top() 
        # end_first_leg       = ( (1+dist_top_uav_to_center_group)*UP + 1.5*LEFT)


        circle1 = always_redraw(
            lambda: Circle(
                radius = r.get_value(), 
                color=ORANGE,
            ).shift(lane_boundary + ((r.get_value()+s/2)*LEFT))
        )
        arc1 = always_redraw(
            lambda: Arc(
                radius = r.get_value(), 
                color=ORANGE,
                start_angle = 0,
                angle = get_theta1()
            ).shift(lane_boundary + ((r.get_value()+s/2)*LEFT))
        )
        arc1_inv = always_redraw(
            lambda: DashedVMobject(

                Arc(
                    radius = r.get_value(), 
                    color=ORANGE,
                    start_angle = get_theta1(),
                    angle = 2*math.pi - get_theta1(),
                ).shift(lane_boundary + ((r.get_value()+s/2)*LEFT)
                ).set_opacity(0.25),
                num_dashes=20,
                dashed_ratio=0.5,
            ) 
        )
        arc1_center = always_redraw(
            lambda: Dot(
                point = lane_boundary + (r.get_value()+s/2)*LEFT,
                color = ORANGE
            )
        )

        arc1_radius_arrow = always_redraw(
            lambda: Arrow(
                start = lane_boundary + (r.get_value()+s/2)*LEFT,
                end = lane_boundary + (r.get_value()+s/2)*LEFT + r.get_value()*math.cos(get_theta1())*UP + r.get_value()*math.sin(get_theta1())*RIGHT,
                color=ORANGE,
                buff=0
            )
        )

        arc2 = always_redraw(
            lambda: Arc(
                radius = r.get_value(), 
                color=ORANGE,
                start_angle = -get_theta1(),
                angle = math.pi + 2*get_theta1()
            ).shift(lane_boundary + (get_dist()*UP))
        )
        arc2_inv = always_redraw(
            lambda: DashedVMobject(

                Arc(
                    radius = r.get_value(), 
                    color=ORANGE,
                    start_angle = math.pi + get_theta1(),
                    angle = math.pi - 2*get_theta1(),
                ).shift(lane_boundary + (get_dist()*UP)
                ).set_opacity(0.25),
                num_dashes=20,
                dashed_ratio=0.5,
            ) 
        )
        
        arc3 = always_redraw(
            lambda: Arc(
                radius = r.get_value(), 
                color=ORANGE,
                start_angle = math.pi-get_theta1(),
                angle = get_theta1()
            ).shift(lane_boundary + ((r.get_value()+s/2)*RIGHT))
        )
        arc3_inv = always_redraw(
            lambda: DashedVMobject(

                Arc(
                    radius = r.get_value(), 
                    color=ORANGE,
                    start_angle = math.pi,
                    angle = 2*math.pi - get_theta1(),
                ).shift(lane_boundary + ((r.get_value()+s/2)*RIGHT)
                ).set_opacity(0.25),
                num_dashes=20,
                dashed_ratio=0.5,
            ) 
        )

        r_label = DecimalNumber(
            r.get_value(),
            num_decimal_places=1,
            include_sign=False,
            color=ORANGE
        )
        def update_radius_label(m):
            m.set_value(r.get_value())
            m.next_to(arc1_radius_arrow, LEFT, buff=0.1)

            def clamp(n, minimum, maximum):
                return min(maximum, max(n, minimum))

            min_text_height = 0.1
            min_r = 1
            max_text_height = 1
            max_r = 6

            text_height = (max_text_height-min_text_height)/(max_r-min_r)*r.get_value()
            m.set_height(clamp(text_height, min_text_height, max_text_height))

        r_label.add_updater(update_radius_label)

        self.add(r, r_label)

        self.add(
            arc1, arc1_inv, arc1_center, arc1_radius_arrow,
            arc2, arc2_inv, 
            arc3, arc3_inv
        )


        # turn_rot_point_dot = Dot(point=turn_rotation_point, color=RED)
        # self.add(turn_rot_point_dot)

        # self.play(
        #     Succession(
        #         # 1. Shift upwards
        #         ApplyMethod(uav_group.move_to, end_first_leg, rate_func=linear),
                
        #         # 2. Rotate
        #         Rotate(
        #             uav_group, 
        #             angle=-PI, 
        #             about_point=first_rotation_point,
        #             rate_func=linear
        #         ),
        #     )
        # )

        self.play(r.animate.set_value(1.0))
        self.play(r.animate.set_value(0.8))
        self.play(r.animate.set_value(2.0))
        self.play(r.animate.set_value(1.0))
        # End the animation
        self.wait(10)


class LimitingBeamCase(BaseScene):

    def construct(self):

        # Add UAV and it's FOV
        uav_group = UAV(fov_width=self.lane_width, fov_deg=35, w_beam_det_fov=True)
        self.add(uav_group)

        # uav_group.next_to(self.search_area, DOWN, aligned_edge=LEFT, buff=0)
        uav_group.next_to(self.search_area, DOWN, buff=0)
        uav_group.shift(self.lane_width * self.N_LANES/2 * LEFT + self.lane_width*0.5*RIGHT)

        # Instantiate target
        tgt = DesignTarget(debug=True)
        tgt.rotate(math.pi/2)
        # tgt.move_to(uav_group.get_edge_center(UP)).shift(uav_group.width/2*RIGHT, aligned_edge=LEFT)
        tgt.move_to(uav_group.get_corner(UR), aligned_edge=LEFT)
        self.add(tgt)

        # End the animation
        self.wait(20)



    def construct(self):
        ship = SVGMobject('./www/frigate.svg')
        ship.scale(2)
        # ship.set_color(GRAY)

        self.play(Create(ship))
        ship.center()
        stern = ship.get_left()
        # self.play(ship.animate.rotate(PI), about_point=stern)
        self.play(ship.animate.rotate(PI), axis=UP)
        self.wait(10)