from manim import *

class sensorGapWhenTurning(Scene):
    def construct(self):

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
        # self.play(Create(search_area))
        self.add(search_area)


        # Define the path for the UAV
        # Create lanes in the search area
        lane_width = search_area.width / N_LANES

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


        # Create the UAV as a triangle
        uav = Triangle(color=YELLOW, fill_opacity=1).scale(0.2).move_to(2*DOWN + LEFT * lane_width/2)

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
                # # 1. Move to start
                # ApplyMethod(uav_group.move_to, start_first_leg, rate_func=linear),
                
                # 2. Shift upwards (using ApplyMethod to avoid overwriting)
                ApplyMethod(uav_group.move_to, end_first_leg, rate_func=linear),
                
                # 3. Rotate (We use a lambda or direct property to ensure it rotates 
                # around where the UAV IS after the previous steps)
                Rotate(
                    uav_group, 
                    angle=-PI, 
                    about_point=turn_rotation_point,
                    rate_func=linear
                ),
                
                # 4. Move to next lane
                # ApplyMethod(uav_group.move_to, end_second_leg
            )
        )

        # Draw sensor gap
        not_covered_gap = Polygon(
            uav.get_bottom(), 
            uav.get_bottom() + LEFT*lane_width/2, 
            uav.get_bottom() + LEFT*lane_width/2 + (uav.get_bottom()-fov.get_bottom())*DOWN,
            stroke_width=0.5
        ).set_fill(WHITE, opacity=0.3)
        not_covered_level_gap = Polygon(
            uav.get_bottom(), 
            uav.get_bottom() + RIGHT*lane_width/2, 
            uav.get_bottom() + RIGHT*lane_width/2 + (uav.get_bottom()-fov.get_bottom())*DOWN,
            stroke_width=0.5
        ).set_fill(WHITE, opacity=0.3)
        self.play(FadeIn(not_covered_gap), FadeIn(not_covered_level_gap))

        not_covered_text = Text('Not Covered', color=BLUE, font_size=20).next_to(search_area, UP).shift(1*LEFT)
        not_covered_arrow = Arrow(not_covered_text.get_bottom(), not_covered_gap.get_center(), color=BLUE)

        not_covered_level_text = Text('Not Covered\nStraight/Level', color=BLUE, font_size=20).next_to(search_area, UP).shift(2*RIGHT)
        not_covered_level_arrow = Arrow(not_covered_level_text.get_bottom(), not_covered_level_gap.get_center(), color=BLUE)


        self.play(Write(not_covered_text), Write(not_covered_arrow), Write(not_covered_level_text), Write(not_covered_level_arrow))


        # End the animation
        self.wait(10)



class ShortLateralOffsetTurn(Scene):
    def construct(self):

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
        # self.play(Create(search_area))
        self.add(search_area)


        # Define the path for the UAV
        # Create lanes in the search area
        lane_width = search_area.width / N_LANES

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
        self.add(lane_boundaries, flight_paths)


        # Create the UAV as a triangle
        uav = Triangle(color=YELLOW, fill_opacity=1).scale(0.2).move_to(2*DOWN + LEFT * lane_width/2)

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
                # # 1. Move to start
                # ApplyMethod(uav_group.move_to, start_first_leg, rate_func=linear),
                
                # 2. Shift upwards (using ApplyMethod to avoid overwriting)
                ApplyMethod(uav_group.move_to, end_first_leg, rate_func=linear),
                
                # 3. Rotate (We use a lambda or direct property to ensure it rotates 
                # around where the UAV IS after the previous steps)
                Rotate(
                    uav_group, 
                    angle=-PI, 
                    about_point=turn_rotation_point,
                    rate_func=linear
                ),
                
                # 4. Move to next lane
                # ApplyMethod(uav_group.move_to, end_second_leg
            )
        )

        # Draw sensor gap
        not_covered_gap = Polygon(
            uav.get_bottom(), 
            uav.get_bottom() + LEFT*lane_width/2, 
            uav.get_bottom() + LEFT*lane_width/2 + (uav.get_bottom()-fov.get_bottom())*DOWN,
            stroke_width=0.5
        ).set_fill(WHITE, opacity=0.3)
        not_covered_level_gap = Polygon(
            uav.get_bottom(), 
            uav.get_bottom() + RIGHT*lane_width/2, 
            uav.get_bottom() + RIGHT*lane_width/2 + (uav.get_bottom()-fov.get_bottom())*DOWN,
            stroke_width=0.5
        ).set_fill(WHITE, opacity=0.3)
        self.play(FadeIn(not_covered_gap), FadeIn(not_covered_level_gap))

        not_covered_text = Text('Not Covered', color=BLUE, font_size=20).next_to(search_area, UP).shift(1*LEFT)
        not_covered_arrow = Arrow(not_covered_text.get_bottom(), not_covered_gap.get_center(), color=BLUE)

        not_covered_level_text = Text('Not Covered\nStraight/Level', color=BLUE, font_size=20).next_to(search_area, UP).shift(2*RIGHT)
        not_covered_level_arrow = Arrow(not_covered_level_text.get_bottom(), not_covered_level_gap.get_center(), color=BLUE)


        self.play(Write(not_covered_text), Write(not_covered_arrow), Write(not_covered_level_text), Write(not_covered_level_arrow))


        # End the animation
        self.wait(10)


