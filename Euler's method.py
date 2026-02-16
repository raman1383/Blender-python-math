import bpy
import math

# ==========================================================
# USER DIFFERENTIAL EQUATION
# ==========================================================

def f(x, y):
    return x - y  # Change this freely


# ==========================================================
# PARAMETERS
# ==========================================================

x_min, x_max = -5, 5
y_min, y_max = -5, 5

grid_spacing = 0.8
segment_length = 0.6
segment_thickness = 0.05

dt = 0.05  # Euler step per frame


# ==========================================================
# CLEAN SCENE
# ==========================================================

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()


# ==========================================================
# DIRECTION FIELD
# ==========================================================

x = x_min
while x <= x_max:
    y = y_min
    while y <= y_max:
        
        slope = f(x, y)
        angle = math.atan(slope)
        
        bpy.ops.mesh.primitive_plane_add(size=1, location=(x, y, 0))
        obj = bpy.context.object
        
        obj.scale[0] = segment_length
        obj.scale[1] = segment_thickness
        obj.rotation_euler[2] = angle
        
        y += grid_spacing
    x += grid_spacing


# ==========================================================
# CREATE DRAGGABLE BALL
# ==========================================================

bpy.ops.mesh.primitive_uv_sphere_add(radius=0.2, location=(0, 0, 0))
ball = bpy.context.object
ball.name = "FlowBall"

ball["prev_loc"] = ball.location[:]


# ==========================================================
# CREATE TRAIL CURVE
# ==========================================================

curve_data = bpy.data.curves.new("BallTrail", 'CURVE')
curve_data.dimensions = '3D'
curve_data.bevel_depth = 0.05
curve_data.use_radius = True   # CRUCIAL

spline = curve_data.splines.new('POLY')
spline.points.add(0)
spline.points[0].co = (*ball.location, 1)

trail_obj = bpy.data.objects.new("BallTrailObj", curve_data)
bpy.context.collection.objects.link(trail_obj)


# ==========================================================
# FRAME HANDLER (FLOW SIMULATION)
# ==========================================================

def create_new_trail(start_location):
    
    # Create unique name
    trail_index = len([obj for obj in bpy.data.objects if obj.name.startswith("BallTrail")])
    trail_name = f"BallTrail_{trail_index}"
    
    curve_data = bpy.data.curves.new(trail_name, 'CURVE')
    curve_data.dimensions = '3D'
    curve_data.bevel_depth = 0.05
    curve_data.use_radius = True
    
    spline = curve_data.splines.new('POLY')
    spline.points.add(0)
    spline.points[0].co = (*start_location, 1)
    
    trail_obj = bpy.data.objects.new(trail_name, curve_data)
    bpy.context.collection.objects.link(trail_obj)
    
    return trail_obj

    

def flow_ball(scene):
    
    ball = bpy.data.objects.get("FlowBall")
    if ball is None:
        return
    
    # Get current active trail from ball
    trail_name = ball.get("active_trail")
    
    if trail_name is None or trail_name not in bpy.data.objects:
        trail = create_new_trail(ball.location)
        ball["active_trail"] = trail.name
    else:
        trail = bpy.data.objects[trail_name]

    
    x, y, z = ball.location
    slope = f(x, y)
    
    # ----- Euler motion -----
    dx = dt
    dy = dt * slope
    
    new_x = x + dx
    new_y = y + dy
    
    # ----- Detect Manual Move -----
    prev = ball["prev_loc"]
    x, y, z = ball.location
    
    dist = math.sqrt(
        (x - prev[0])**2 +
        (y - prev[1])**2
    )
    
    if dist > 0.5:
        trail = create_new_trail(ball.location)
        ball["active_trail"] = trail.name
        ball["prev_loc"] = ball.location[:]
        return

    
    # Apply motion
    ball.location.x = new_x
    ball.location.y = new_y
    
    # ----- Speed -----
    curr = ball.location[:]
    speed = math.sqrt(
        (curr[0] - prev[0])**2 +
        (curr[1] - prev[1])**2
    )
    
    ball["prev_loc"] = curr
    
    # ----- Add Trail Point -----
    spline = trail.data.splines[0]
    spline.points.add(1)
    spline.points[-1].co = (*curr, 1)
    spline.points[-1].radius = speed * 8
    
    trail.data.update()


# ==========================================================
# REMOVE OLD HANDLER (SAFE WAY)
# ==========================================================

bpy.app.handlers.frame_change_pre[:] = [
    h for h in bpy.app.handlers.frame_change_pre
    if h.__name__ != "flow_ball"
]

bpy.app.handlers.frame_change_pre.append(flow_ball)

print("Direction field + live trail system ready.")
