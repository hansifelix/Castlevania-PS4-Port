// Linux-only stub for the PS4 graphics helper, to exercise console logic.
#pragma once
#include <cstdlib>
struct Color {int r,g,b;};
class Scene2D {
public:
  Scene2D(int,int,int){}
  bool Init(int,int){return true;}
  void SetActiveFrameBuffer(int){}
  void FrameBufferFill(Color){}
  void DrawRectangle(int,int,int,int,Color){}
  void SubmitFlip(int){}
  void FrameWait(int){std::exit(0);} // one frame then exit host mock
};
