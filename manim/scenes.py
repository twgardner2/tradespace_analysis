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

class BaseScene(MovingCameraScene):
    def setup(self):
        # config.frame_height = 6
        # config.frame_width = 8

        WIDTH = 4
        HEIGHT = 4
        self.N_LANES = 4

        # Create the box representing the search area
        search_perimeter = Rectangle(width=WIDTH, height=HEIGHT, color=BLUE).shift(DOWN * 1)

        # Create lanes in the search area
        lane_width = search_perimeter.width / self.N_LANES

        lane_boundaries = VGroup()
        for i in range(1, self.N_LANES):
            lane_x = search_perimeter.get_left()[0] + lane_width * i
            boundary = Line(
                start=search_perimeter.get_bottom() + RIGHT * lane_x,
                end=search_perimeter.get_top() + RIGHT * lane_x,
                color=BLUE,
                stroke_width=1,
                # stroke_opacity=0.5
            )
            lane_boundaries.add(boundary)

        # Add dotted flight paths in the center of each lane
        flight_paths = VGroup()
        for lane in lane_boundaries:
            flight_path = DashedLine(
                start=lane.get_start() + 0.5 * LEFT,
                end=lane.get_end() + 0.5 * LEFT,
                color=WHITE,
                dash_length=0.2,
            )
            flight_paths.add(flight_path)

        flight_paths.add(
            DashedLine(
                start=flight_paths[-1].get_start() + lane_width * RIGHT,
                end=flight_paths[-1].get_end() + lane_width * RIGHT,
                color=WHITE,
                dash_length=0.2,
            )
        )

        # Attach for later access
        self.search_perimeter = search_perimeter
        self.lane_boundaries = lane_boundaries
        self.flight_paths = flight_paths
        self.lane_width = lane_width

        # Group them together for convenient transforms/access
        self.search_box = VGroup(self.search_perimeter, self.lane_boundaries, self.flight_paths)

        # Add to scene
        self.add(self.search_box)



class BaseSceneSemiCircleTurn(MovingCameraScene):
    def setup(self):
        # config.frame_height = 6
        # config.frame_width = 8

        WIDTH = 5
        HEIGHT = 4
        self.N_LANES = 5

        # Create the box representing the search area
        search_perimeter = Rectangle(width=WIDTH, height=HEIGHT, color=BLUE).shift(DOWN * 1)

        # Create lanes in the search area
        lane_width = search_perimeter.width / self.N_LANES

        lane_boundaries = VGroup()
        for i in range(1, self.N_LANES-1):
            lane_x = search_perimeter.get_left()[0] + lane_width * i
            boundary = Line(
                start=search_perimeter.get_bottom() + RIGHT * lane_x,
                end=search_perimeter.get_top() + RIGHT * lane_x,
                color=BLUE,
                stroke_width=1,
                # stroke_opacity=0.5
            )
            lane_boundaries.add(boundary)
        print(lane_boundaries)

        # Add dotted flight paths in the center of each lane
        flight_paths = VGroup()

        # First N_LANES-1 normal lanes
        # for lane in lane_boundaries:
        #     flight_path = DashedLine(
        #         start=lane.get_start() + 0.5 * LEFT,
        #         end=lane.get_end() + 0.5 * LEFT,
        #         color=WHITE,
        #         dash_length=0.2,
        #     )
        #     flight_paths.add(flight_path)
        for i in range(len(lane_boundaries)):
            if i<len(lane_boundaries):
                flight_path = DashedLine(
                    start=lane_boundaries[i].get_start() + 0.5 * LEFT,
                    end=lane_boundaries[i].get_end() + 0.5 * LEFT,
                    color=WHITE,
                    dash_length=0.2,
                )
            else:
                flight_path = DashedLine(
                    start=lane_boundaries[i].get_start() + 0.5 * LEFT,
                    end=lane_boundaries[i].get_end() + 0.5 * LEFT,
                    color=WHITE,
                    dash_length=0.2,
                )
                
            flight_paths.add(flight_path)


        # Rightmost lane is DOUBLE width → center is shifted right by +lane_width
        flight_paths.add(
            DashedLine(
                start=flight_paths[-1].get_start() + 1.5*lane_width * RIGHT,
                end=flight_paths[-1].get_end() + 1.5*lane_width * RIGHT,
                color=WHITE,
                dash_length=0.2,
            )
        )

        # Attach for later access
        self.search_perimeter = search_perimeter
        self.lane_boundaries = lane_boundaries
        self.flight_paths = flight_paths
        self.lane_width = lane_width

        # Group them together for convenient transforms/access
        self.search_box = VGroup(self.search_perimeter, self.lane_boundaries, self.flight_paths)

        # Add to scene
        self.add(self.search_box)



class a_LawnMower(BaseScene):
    def construct(self):

        self.camera.frame_height = 6.5
        self.camera.frame_center = [0, -1, 0]

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



class c_DetectionRangesWGraph(Scene):
    def construct(self):
        # --- Parameters ---
        TGT_LENGTH = 160  # m
        TGT_HEIGHT = 40   # m
        RES = 480
        JOHNSON = 8
        FOV_RAD = 60 * 2 * PI / 360
        
        TGT_POS = LEFT * 3 + UP * 2.5
        MAX_DET_RNG = (TGT_LENGTH * RES) / (JOHNSON * FOV_RAD)
        SCALE_FACTOR = 4.5 / MAX_DET_RNG 

        # --- Functions ---
        def get_det_rng(angle):
            tgt_x = max(TGT_HEIGHT, abs(TGT_LENGTH * math.cos(angle)))
            return (tgt_x * RES) / (JOHNSON * FOV_RAD)

        def world_angle_to_bow_label(world_angle):
            world_deg = (world_angle * 180 / PI) % 360
            bow_deg = (world_deg - 270) % 360
            if bow_deg == 0: return "0"
            if bow_deg == 180: return "180"
            if bow_deg < 180: return f"Starboard {int(round(bow_deg))}"
            return f"Port {int(round(360 - bow_deg))}"

        # --- Trackers ---
        tgt_aob = ValueTracker(0)
        tgt_aob_ref = ValueTracker(0)

        # --- Labels ---
        label_fs = 28
        value_fs = 28
        col_w = 3.5

        def create_cell(content_str, is_label=True):
            txt = Text(content_str, font_size=label_fs if is_label else value_fs)
            frame = Rectangle(width=col_w, height=0.5, stroke_opacity=0, fill_opacity=0)
            txt.move_to(frame.get_left(), aligned_edge=LEFT)
            return VGroup(frame, txt)

        header_labels = VGroup(
            create_cell("AOB", is_label=True),
            create_cell("Tgt Length Cross", is_label=True),
            create_cell("Tgt Height", is_label=True),
        ).arrange(RIGHT, buff=0.2).to_edge(UP, buff=0.2).shift(LEFT * 0.5)

        header_values = always_redraw(
            lambda: VGroup(
                create_cell(world_angle_to_bow_label(tgt_aob.get_value()), is_label=False),
                create_cell(f"{abs(TGT_LENGTH * math.cos(tgt_aob.get_value())):.0f} m", is_label=False),
                create_cell(f"{TGT_HEIGHT} m", is_label=False),
            ).arrange(RIGHT, buff=0.2).next_to(header_labels, DOWN, buff=0.1, aligned_edge=LEFT)
        )
        self.add(header_labels, header_values)

        # --- Plot ---
        axes = Axes(
            x_range=[0, 2 * PI, PI / 2],
            y_range=[0, MAX_DET_RNG * 1.1, 2000],
            x_length=5,
            y_length=4,
            axis_config={"include_tip": False, "font_size": 20},
        ).to_edge(RIGHT, buff=0.5).shift(DOWN * 0.5)

        det_curve = axes.plot(lambda x: get_det_rng(x), color=YELLOW, x_range=[0, 2 * PI])
        dot = always_redraw(lambda: Dot(color=RED).move_to(
            axes.c2p(tgt_aob.get_value(), get_det_rng(tgt_aob.get_value()))
        ))
        self.add(axes, det_curve, dot)

        # --- Target ---
        tgt = Polygon(
            *[0.3 * np.array(p) for p in [(1.8,0,0), (1.2,0.35,0), (-1.8,0.35,0), (-1.8,-0.35,0), (1.2,-0.35,0)]],
            stroke_color=WHITE, fill_color=GRAY, fill_opacity=0.35
        ).move_to(TGT_POS)
        
        tgt.add_updater(lambda m: m.rotate(tgt_aob.get_value() - tgt_aob_ref.get_value()).move_to(TGT_POS))
        tgt.add_updater(lambda m: tgt_aob_ref.set_value(tgt_aob.get_value()))
        self.add(tgt)

        # --- UAV and FOV ---
        uav = UAV(fov_width=1, fov_deg=25, w_height_det_fov=False, w_beam_det_fov=False)
        
        def update_uav(m):
            current_rng_screen = get_det_rng(tgt_aob.get_value()) * SCALE_FACTOR
            m.move_to([TGT_POS[0], TGT_POS[1] - current_rng_screen, 0])

        # FIX: Explicitly set position BEFORE adding to scene to prevent origin-jump
        initial_rng_screen = get_det_rng(0) * SCALE_FACTOR
        uav.move_to([TGT_POS[0], TGT_POS[1] - initial_rng_screen, 0])
        
        uav.add_updater(update_uav)
        
        fov_cone = always_redraw(lambda: Polygon(
            uav.get_top(),
            uav.get_top() + (get_det_rng(tgt_aob.get_value()) * SCALE_FACTOR) * UP + (get_det_rng(tgt_aob.get_value()) * SCALE_FACTOR * math.tan(FOV_RAD/2)) * LEFT,
            uav.get_top() + (get_det_rng(tgt_aob.get_value()) * SCALE_FACTOR) * UP + (get_det_rng(tgt_aob.get_value()) * SCALE_FACTOR * math.tan(FOV_RAD/2)) * RIGHT,
            stroke_color=YELLOW, fill_color=YELLOW, fill_opacity=0.15
        ))
        
        self.add(uav, fov_cone)

        # --- Animation ---
        self.wait(1)
        self.play(tgt_aob.animate.set_value(2*PI), run_time=10, rate_func=linear)
        self.wait(2)



class d_SemiCircleTurn(BaseSceneSemiCircleTurn):
    def construct(self):
        
        # Set camera view
        orig_height = self.camera.frame_height
        orig_width  = self.camera.frame_width

        self.camera.frame_height = 5
        self.camera.frame_width  = self.camera.frame_height * orig_width/orig_height
        self.camera.frame_center = [0, 1, 0]

        # Add UAVs to the scene
        uav1 = UAV(fov_width=self.lane_width, fov_deg = 35,  w_height_det_fov = False, w_beam_det_fov=False)
        uav1.scale(0.9).move_to(2*DOWN + 1.25*LEFT * (3/2)*uav1.fov_width)
        uav2 = UAV(fov_width=self.lane_width, fov_deg = 35,  w_height_det_fov = False, w_beam_det_fov=False)
        uav2.scale(0.9).move_to(2*DOWN + 0   *RIGHT * (3/2)*uav2.fov_width)
        self.add(uav1, uav2)

        uav_offset = (uav1.get_top() - uav1.get_center())

        end_first_leg              =   2*LEFT  + 1*UP + uav_offset*DOWN
        end_first_leg_turn_point   = 1.5*LEFT  + 1*UP 
        start_second_leg           =   1*LEFT  + 1*UP + uav_offset*DOWN
        end_second_leg             = 0.5*LEFT  + 3*DOWN + uav_offset*UP
        end_second_leg_turn_point  = 0  *LEFT  + 3*DOWN 
        end_third_leg              =   0*RIGHT + 1*UP + uav_offset*DOWN
        end_third_leg_turn_point1  = end_third_leg + 0.5*RIGHT + uav_offset*UP
        end_third_leg_turn_point2  = end_third_leg +   1*RIGHT + uav_offset*UP
        start_fourth_leg           = 1.5*RIGHT + 1*UP + uav_offset*DOWN
        end_fourth_leg             = 1.5*RIGHT + 3*DOWN + uav_offset*UP

        # dot3 = Dot(end_third_leg_turn_point1, color=RED)
        # dot4 = Dot(end_third_leg_turn_point2, color=RED)
        # self.add(dot3, dot4)


        # Annotations of first turn
        brace = BraceBetweenPoints(end_first_leg, start_second_leg, direction=UP, color=ORANGE)
        brace_label = MathTex('S', font_size=38, color=ORANGE)
        brace_label.next_to(brace, direction=UP)

        # Semi-circle tangent to the brace endpoints (diameter = brace endpoints)
        semi_circle = ArcBetweenPoints(
            end_first_leg + uav_offset*UP,
            start_second_leg + uav_offset*UP,
            angle=-PI,
            color=ORANGE,
        )
        # Radius line from the semi-circle center to the point 45° from the +x axis
        semi_circle_center = 0.5 * (
            end_first_leg + start_second_leg
        ) + (uav1.get_top() - uav1.get_center()) * UP

        semi_circle_radius = 0.5 * np.linalg.norm(end_first_leg - start_second_leg)
        semi_circle_radius_line = Line(
            semi_circle_center,
            semi_circle_center + semi_circle_radius * (np.cos(PI / 4) * RIGHT + np.sin(PI / 4) * UP),
            color=ORANGE,
        )
        semi_circle_radius_label = MathTex('R', font_size=38, color=ORANGE)
        semi_circle_radius_label.next_to(semi_circle_radius_line, direction=[1,1,0], buff=0.1)
        
        # Annotations of second turn
        brace2 = BraceBetweenPoints(end_third_leg, start_fourth_leg, direction=UP, color=ORANGE)
        brace2_label = MathTex('S', font_size=38, color=ORANGE)
        brace2_label.next_to(brace2, direction=UP)

        # Semi-circle tangent to the brace endpoints (diameter = brace endpoints)
        semi_circle2 = semi_circle.copy().shift(2*RIGHT)
        semi_circle2_center = end_third_leg + 0.5*RIGHT + uav_offset*UP

        semi_circle2_radius_line = Line(
            semi_circle2_center,
            semi_circle2_center + semi_circle_radius * (np.cos(PI / 4) * RIGHT + np.sin(PI / 4) * UP),
            color=ORANGE,
        )
        semi_circle2_radius_label = MathTex('R', font_size=38, color=ORANGE)
        semi_circle2_radius_label.next_to(semi_circle2_radius_line, direction=[1,1,0], buff=0.1)



        # Animations
        self.play(
            ApplyMethod(uav1.move_to, end_first_leg, rate_func=linear),
            ApplyMethod(uav2.move_to, end_third_leg, rate_func=linear),
        )

        # Fade in braces after the first move_to
        # self.play(FadeIn(brace), FadeIn(brace_label),FadeIn(brace2), FadeIn(brace2_label))
        self.play(Create(brace), Create(brace_label),Create(brace2), Create(brace2_label))
        self.wait(1)
        self.play(FadeOut(brace), FadeOut(brace2))
        self.play(
            ApplyMethod(brace_label.move_to,   brace_label.get_center() + 0.5*UP + 0.5*LEFT, rate_func=linear),
            ApplyMethod(brace2_label.move_to, brace2_label.get_center() + 0.5*UP + 0.5*LEFT, rate_func=linear),
        )
        self.play(
            Create(semi_circle), 
            Create(semi_circle_radius_line), 
            Create(semi_circle_radius_label),
            Create(semi_circle2), 
            Create(semi_circle2_radius_line), 
            Create(semi_circle2_radius_label)
        )
        self.wait(1)
        self.play(
            # FadeOut(semi_circle), 
            FadeOut(semi_circle_radius_line),
            # FadeOut(semi_circle2), 
            FadeOut(semi_circle2_radius_line),
        )
        eq_gap = 0.32   # horizontal gap for "="
        gt_gap = 0.32   # horizontal gap for ">"

        self.play(
            ApplyMethod(
                semi_circle_radius_label.move_to,
                brace_label.get_center() + (0.5 + eq_gap) * RIGHT,
                rate_func=linear,
            ),
            ApplyMethod(
                semi_circle2_radius_label.move_to,
                brace2_label.get_center() + (0.5 + gt_gap) * RIGHT,
                rate_func=linear,
            ),
        )

        turn1_eq = MathTex('=', font_size=38, color=ORANGE)
        turn2_eq = MathTex('>', font_size=38, color=ORANGE)

        # Place "=" and ">" between their respective S and R labels
        turn1_eq.move_to(midpoint(brace_label.get_center(), semi_circle_radius_label.get_center()))
        turn2_eq.move_to(midpoint(brace2_label.get_center(), semi_circle2_radius_label.get_center()))

        self.play(FadeIn(turn1_eq), FadeIn(turn2_eq))

        # Break semi_circle2 into two halves, shift right half, and connect with a straight segment
        semi_circle2_left = ArcBetweenPoints(
            end_third_leg + uav_offset * UP,
            semi_circle2_center + semi_circle_radius * UP,
            angle=-PI / 2,
            color=ORANGE,
        )
        semi_circle2_right = ArcBetweenPoints(
            semi_circle2_center + semi_circle_radius * UP,
            semi_circle2_center + semi_circle_radius * RIGHT,
            # start_fourth_leg + uav_offset * UP,
            angle=-PI / 2,
            color=ORANGE,
        )

        # Swap the single arc for the two-half arcs without a visible pop
        semi_circle2_left.set_z_index(semi_circle2.get_z_index())
        semi_circle2_right.set_z_index(semi_circle2.get_z_index())

        self.add(semi_circle2_left, semi_circle2_right)
        self.remove(semi_circle2)

        # Expand the right half while continuously drawing a connector so the path never "breaks"
        connector = always_redraw(
            lambda: Line(
            semi_circle2_left.get_end(),
            semi_circle2_right.get_start(),
            color=ORANGE,
            )
        )
        self.add(connector)

        self.play(
            semi_circle2_right.animate.shift(0.5 * RIGHT),
            run_time=0.75,
            rate_func=smooth,
        )


        # Continue with the turn
        self.play(
            Rotate(
                uav1,
                angle=-PI,
                about_point=end_first_leg_turn_point,
                rate_func=linear,
                run_time=2
            ),
            Succession(
                Rotate(
                    uav2,
                    angle=-PI / 2,
                    about_point=end_third_leg_turn_point1,
                    rate_func=linear,
                    run_time=1
                ),
                ApplyMethod(
                    uav2.move_to,
                    end_third_leg_turn_point2 + 0.5 * UP,
                    rate_func=linear,
                    run_time=1
                ),
                Rotate(
                    uav2,
                    angle=-PI / 2,
                    about_point=end_third_leg_turn_point2,
                    rate_func=linear,
                    run_time=1
                ),
                # run_time=2
            )
        )


        self.wait(2)




class e_ShortLateralOffsetTurn(BaseScene):
    def construct(self):
        # 1. Setup Parameters & Shift
        scene_shift = 2 * DOWN
        self.search_box.shift(scene_shift)
        
        S_OFFSET = 1  # s
        r_tracker = ValueTracker(0.6)
        
        # Define the anchor where the turn starts
        lane_boundary = (2 * UP + 1 * LEFT) + scene_shift

        # 2. UAV Setup
        uav_group = UAV(fov_width=self.lane_width, fov_deg=35)
        uav_group.scale(0.9).move_to(
            1 * UP
            + (uav_group.uav.get_top() - uav_group.uav.get_center()) * DOWN
            + LEFT * (1.5) * uav_group.fov_width
            + scene_shift
        )

        # 3. Create the Orange Path (Always Redrawn)
        def create_orange_path():
            r = r_tracker.get_value()
            
            # Math
            theta1 = math.acos((r + S_OFFSET / 2) / (2 * r))
            dist_y = math.sqrt(max(0, (2 * r)**2 - (r + S_OFFSET / 2)**2))
            
            # Center Points
            c1 = lane_boundary + (r + S_OFFSET / 2) * LEFT
            c2 = lane_boundary + dist_y * UP
            c3 = lane_boundary + (r + S_OFFSET / 2) * RIGHT

            # Arcs (Solid)
            a1 = Arc(radius=r, start_angle=0, angle=theta1, color=ORANGE).shift(c1)
            a2 = Arc(radius=r, start_angle=-theta1, angle=PI + 2*theta1, color=ORANGE).shift(c2)
            a3 = Arc(radius=r, start_angle=PI-theta1, angle=theta1, color=ORANGE).shift(c3)

            # Arcs (Dashed/Ghost)
            a1_ghost = DashedVMobject(Arc(radius=r, start_angle=theta1, angle=TAU-theta1).shift(c1), num_dashes=20).set_opacity(0.25)
            a2_ghost = DashedVMobject(Arc(radius=r, start_angle=PI+theta1, angle=PI-2*theta1).shift(c2), num_dashes=10).set_opacity(0.25)
            a3_ghost = DashedVMobject(Arc(radius=r, start_angle=PI, angle=TAU-theta1).shift(c3), num_dashes=20).set_opacity(0.25)

            # Center and Arrow
            center_dot = Dot(c1, color=ORANGE, radius=0.06)
            radius_arrow = Arrow(start=c1, end=c1 + r*math.cos(theta1)*RIGHT + r*math.sin(theta1)*UP, color=ORANGE, buff=0)

            return VGroup(a1, a2, a3, a1_ghost, a2_ghost, a3_ghost, center_dot, radius_arrow)

        orange_path = always_redraw(create_orange_path)

        # 4. Straight Lines (Transitions)
        # Using a simple updater to keep them attached to the UAV if it moves
        uav_nose = uav_group.get_critical_point(Y_AXIS)
        line_out = Line(uav_nose, uav_nose + 1*UP, color=ORANGE)
        line_in = line_out.copy().shift(S_OFFSET * RIGHT)

        # 5. Radius Label & Dynamic Scaling
        r_label = DecimalNumber(r_tracker.get_value(), num_decimal_places=1, color=ORANGE)

        def update_label(m):
            r_val = r_tracker.get_value()
            # Reference the arrow from the always_redraw group
            arrow = orange_path[-1] 
            m.set_value(r_val)
            m.next_to(arrow, LEFT, buff=0.1)
            
            # Dynamic text scaling
            new_h = interpolate(0.1, 1.0, (r_val - 1) / 5)
            m.set_height(max(0.1, min(1.0, new_h)))

        r_label.add_updater(update_label)

        # 6. Add and Play
        self.add(uav_group, orange_path, line_out, line_in, r_label)

        self.play(r_tracker.animate.set_value(1.0))
        self.play(r_tracker.animate.set_value(0.8))
        self.play(r_tracker.animate.set_value(2.0))
        self.play(r_tracker.animate.set_value(1.0))
        self.wait(2)




class f_SensorGapWhenTurning(BaseScene):
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

        not_covered_text = Text('Not Covered', color=BLUE, font_size=20).next_to(self.search_box, UP).shift(2*LEFT + 0.15*UP)
        not_covered_arrow = Arrow(not_covered_text.get_bottom(), not_covered_gap.get_center(), color=BLUE)

        not_covered_level_text = Paragraph(
            'Not Covered', 'Straight & Level', color=BLUE, font_size=20, alignment='center'
        ).next_to(self.search_box, UP).shift(1*RIGHT)
        not_covered_level_arrow = Arrow(not_covered_level_text.get_bottom(), not_covered_level_gap.get_center(), color=BLUE)

        self.play(Write(not_covered_text), Write(not_covered_arrow), Write(not_covered_level_text), Write(not_covered_level_arrow), run_time=TEXT_WRITE_TIME)

        # End the animation
        self.wait(10)

class g_LimitingBeamingCase(BaseScene):

    def construct(self):

        # Set camera view
        orig_height = self.camera.frame_height
        orig_width  = self.camera.frame_width

        self.camera.frame_height = 7
        self.camera.frame_width  = self.camera.frame_height * orig_width/orig_height
        self.camera.frame_center = [0, -2, 0]

        # Add UAV and it's FOV
        uav = UAV(fov_width=self.lane_width, fov_deg=75, w_beam_det_fov=True, w_height_det_fov=True)
        self.add(uav)

        uav.next_to(self.search_box, DOWN, buff=0)
        uav.shift(self.lane_width * self.N_LANES/2 * LEFT + self.lane_width*0.5*RIGHT)

        # Instantiate target
        tgt_heading = PI
        tgt = DesignTarget(debug=False)
        tgt.scale(2)
        tgt.rotate(tgt_heading)
        tgt.move_to(uav.get_corner(UR), aligned_edge=LEFT)
        tgt_continuous_animation = always_redraw(
            lambda: tgt.shift(0.02 * np.array([math.cos(tgt_heading), math.sin(tgt_heading), 0]))
        )
        self.add(tgt)


        dist_top_uav_to_center_group = uav.get_center() - uav.uav.get_top() 
        start_first_leg     = ((2+dist_top_uav_to_center_group)*DOWN + 1.5*LEFT   )
        end_first_leg       = ( (1+dist_top_uav_to_center_group)*UP + 1.5*LEFT)
        turn_rotation_point = ( 1*UP + 1*LEFT            )
        end_second_leg      = ((3+dist_top_uav_to_center_group)*DOWN + 1.5*RIGHT) 


        # Animation
        uav_leg_time = 1.7
        self.play(
            Succession(
                # 1. Shift upwards
                ApplyMethod(uav.move_to, end_first_leg, rate_func=linear, run_time=uav_leg_time),

                # 2. Rotate
                Rotate(
                    uav,
                    angle=-PI,
                    about_point=turn_rotation_point,
                    rate_func=linear
                ),

                # 3. Align the DOWN (bottom) edge of the uav to the DOWN edge of the search_box
                ApplyMethod(uav.align_to, self.search_box, DOWN, rate_func=linear, run_time=0.4*uav_leg_time),
            )
        )
        self.wait(2)

