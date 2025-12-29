
# Convert medium quality .mp4 to .gif
# ffmpeg -i SceneName.mp4 -vf "fps=30,scale=720:-1:flags=lanczos,palettegen" palette.png
# ffmpeg -i SceneName.mp4 -i palette.png -filter_complex "fps=30,scale=720:-1:flags=lanczos[x];[x][1:v]paletteuse" output.gif



from manim import *


TEXT_WRITE_TIME = 1 # seconds

class BaseScene(Scene):
    def setup(self):
                # config.frame_height = 6
        # config.frame_width = 8

        WIDTH = 4
        HEIGHT = 4
        N_LANES = 4

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


        # Define the path for the UAV
        # Create lanes in the search area
        lane_width = search_area.width / N_LANES
        self.lane_width = lane_width

        lane_boundaries = VGroup()
        for i in range(1, N_LANES):
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
        # self.play(Create(lane_boundaries), Create(flight_paths))
        self.add(lane_boundaries, flight_paths)



class SensorGapWhenTurning(BaseScene):
    def construct(self):

        # Create the UAV as a triangle
        uav = Triangle(color=YELLOW, fill_opacity=1).scale(0.2).move_to(2*DOWN + LEFT * self.lane_width/2)

        # Create the sensor field of view as a cone
        fov = VGroup(
            Line(start=uav.get_top(), end=uav.get_center() + UP * 1.5 + LEFT * 0.5, color=YELLOW),
            Line(start=uav.get_top(), end=uav.get_center() + UP * 1.5 + RIGHT * 0.5, color=YELLOW),
            Line(start=uav.get_center() + UP * 1.5 + LEFT * 0.5,
                end=uav.get_center() + UP * 1.5 + RIGHT * 0.5,
                color=YELLOW
            )
        )

        # Group UAV and FOV
        uav_group = VGroup(uav, fov)
        # Add UAV and FOV to the scene
        # self.play(FadeIn(uav_group))
        self.add(uav_group)

        dist_top_uav_to_center_group = uav_group.get_center() - uav.get_top() 
        start_first_leg     = ((2+dist_top_uav_to_center_group)*DOWN + 0.5*LEFT   )
        end_first_leg       = ( (1+dist_top_uav_to_center_group)*UP + 0.5*LEFT)
        turn_rotation_point = ( 1*UP             )
        end_second_leg      = ((3+dist_top_uav_to_center_group)*DOWN + 0.5*RIGHT) 

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
            uav.get_bottom(), 
            uav.get_bottom() + LEFT*self.lane_width/2, 
            uav.get_bottom() + LEFT*self.lane_width/2 + (uav.get_bottom()-fov.get_bottom())*DOWN,
            stroke_width=0.5
        ).set_fill(WHITE, opacity=0.3)
        not_covered_level_gap = Polygon(
            uav.get_bottom(), 
            uav.get_bottom() + RIGHT*self.lane_width/2, 
            uav.get_bottom() + RIGHT*self.lane_width/2 + (uav.get_bottom()-fov.get_bottom())*DOWN,
            stroke_width=0.5
        ).set_fill(WHITE, opacity=0.3)
        self.play(FadeIn(not_covered_gap), FadeIn(not_covered_level_gap))

        not_covered_text = Text('Not Covered', color=BLUE, font_size=20).next_to(self.search_area, UP).shift(1*LEFT + 0.15*UP)
        not_covered_arrow = Arrow(not_covered_text.get_bottom(), not_covered_gap.get_center(), color=BLUE)

        # not_covered_level_text = Text('Not Covered\nStraight/Level', color=BLUE, font_size=20).next_to(self.search_area, UP).shift(2*RIGHT)
        not_covered_level_text = Paragraph(
            'Not Covered', 'Straight/Level', color=BLUE, font_size=20, alignment='center'
        ).next_to(self.search_area, UP).shift(2*RIGHT)
        not_covered_level_arrow = Arrow(not_covered_level_text.get_bottom(), not_covered_level_gap.get_center(), color=BLUE)

        self.play(Write(not_covered_text), Write(not_covered_arrow), Write(not_covered_level_text), Write(not_covered_level_arrow), run_time=TEXT_WRITE_TIME)

        # End the animation
        self.wait(3)



class ShortLateralOffsetTurn(BaseScene):
    def construct(self):

        # Create the UAV as a triangle
        uav = Triangle(color=YELLOW, fill_opacity=1).scale(0.2).move_to(2*DOWN + LEFT * self.lane_width/2)

        # Create the sensor field of view as a cone
        fov = VGroup(
            Line(start=uav.get_top(), end=uav.get_center() + UP * 1.5 + LEFT * 0.5, color=YELLOW),
            Line(start=uav.get_top(), end=uav.get_center() + UP * 1.5 + RIGHT * 0.5, color=YELLOW),
            Line(start=uav.get_center() + UP * 1.5 + LEFT * 0.5,
                end=uav.get_center() + UP * 1.5 + RIGHT * 0.5,
                color=YELLOW
            )
        )

        # Group UAV and FOV
        uav_group = VGroup(uav, fov)
        # Add UAV and FOV to the scene
        # self.play(FadeIn(uav_group))
        self.add(uav_group)

        dist_top_uav_to_center_group = uav_group.get_center() - uav.get_top() 
        start_first_leg     = ((2+dist_top_uav_to_center_group)*DOWN + 0.5*LEFT   )
        end_first_leg       = ( (1+dist_top_uav_to_center_group)*UP + 0.5*LEFT)
        turn_rotation_point = ( 1*UP             )
        end_second_leg      = ((3+dist_top_uav_to_center_group)*DOWN + 0.5*RIGHT) 

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
            uav.get_bottom(), 
            uav.get_bottom() + LEFT*self.lane_width/2, 
            uav.get_bottom() + LEFT*self.lane_width/2 + (uav.get_bottom()-fov.get_bottom())*DOWN,
            stroke_width=0.5
        ).set_fill(WHITE, opacity=0.3)
        not_covered_level_gap = Polygon(
            uav.get_bottom(), 
            uav.get_bottom() + RIGHT*self.lane_width/2, 
            uav.get_bottom() + RIGHT*self.lane_width/2 + (uav.get_bottom()-fov.get_bottom())*DOWN,
            stroke_width=0.5
        ).set_fill(WHITE, opacity=0.3)
        self.play(FadeIn(not_covered_gap), FadeIn(not_covered_level_gap))

        not_covered_text = Text('Not Covered', color=BLUE, font_size=20).next_to(self.search_area, UP).shift(1*LEFT)
        not_covered_arrow = Arrow(not_covered_text.get_bottom(), not_covered_gap.get_center(), color=BLUE)

        not_covered_level_text = Text('Not Covered\nStraight/Level', color=BLUE, font_size=20).next_to(self.search_area, UP).shift(2*RIGHT)
        not_covered_level_arrow = Arrow(not_covered_level_text.get_bottom(), not_covered_level_gap.get_center(), color=BLUE)

        self.play(Write(not_covered_text), Write(not_covered_arrow), Write(not_covered_level_text), Write(not_covered_level_arrow), run_time=TEXT_WRITE_TIME)

        # End the animation
        self.wait(3)
