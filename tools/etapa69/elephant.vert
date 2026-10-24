#version 450
layout(push_constant) uniform Sprite { vec4 rect; vec4 tint; vec4 other; } pc;
layout(location=0) out vec2 p_local;
layout(location=1) out vec4 p_color;
layout(location=2) flat out int p_shape;
const vec2 corner[6] = vec2[6](
 vec2(-1.0,-1.0), vec2(1.0,-1.0), vec2(-1.0,1.0),
 vec2(-1.0,1.0), vec2(1.0,-1.0), vec2(1.0,1.0)
);
void main() {
  vec2 p = corner[gl_VertexIndex];
  gl_Position = vec4(pc.rect.xy + p*pc.rect.zw, 0.0, 1.0);
  p_local=p;
  p_color=pc.tint;
  p_shape=int(pc.other.x+0.5);
}
