#version 450
layout(location=0) in vec2 p_local;
layout(location=1) in vec4 p_color;
layout(location=2) flat in int p_shape;
layout(location=0) out vec4 outColor;
void main(){
  if(p_shape==1 && dot(p_local,p_local)>1.0) discard;
  outColor=p_color;
}
