#include "page_commit_ledger.h"
#include <cassert>
#include <cstdint>
#include <cstdio>
#include <vector>
#include <random>

using lingshu185::CommitLedger;
int main() {
  constexpr std::uint64_t pg=16384;
  CommitLedger x;
  assert(!x.covers(pg,pg*2));
  x.add(pg,pg*3);
  assert(x.covers(pg,pg*2));
  assert(x.covers(pg,pg*3));
  assert(!x.covers(0,pg*3));
  assert(!x.covers(pg,pg*4));
  x.add(pg*3,pg*4);
  assert(x.covers(pg,pg*4));
  assert(x.ranges().size()==1);
  x.add(0,pg);
  assert(x.covers(0,pg*4));
  x.remove(pg,pg*3);
  assert(x.ranges().size()==2);
  assert(x.covers(0,pg));
  assert(!x.covers(0,pg*4));
  assert(x.covers(pg*3,pg*4));
  x.remove(0,pg*4);
  assert(x.ranges().empty());
  x.add(pg*8,pg*12);
  x.add(pg*3,pg*6);
  x.add(pg*5,pg*9);
  assert(x.covers(pg*3,pg*12));
  assert(x.ranges().size()==1);
  x.remove(pg*6,pg*8);
  assert(!x.covers(pg*4,pg*10));
  assert(x.covers(pg*8,pg*12));
  assert(!x.covers(0,0));
  std::puts("LINGSHU185_LEDGER_HAND_CASES=PASS");

  // Deterministic property test: compare interval ledger against a bitset
  // representing 128 virtual pages, across 20,000 synthetic operations.
  std::mt19937 rng(185);
  std::vector<bool> oracle(128,false);
  CommitLedger ledger;
  for (unsigned step=0;step<20000;++step) {
    const auto a=static_cast<unsigned>(rng()%128);
    const auto b=a+1+static_cast<unsigned>(rng()%(128-a));
    const unsigned op=rng()%3;
    if(op==0) {ledger.add(a*pg,b*pg);for(auto i=a;i<b;++i)oracle[i]=true;}
    else if(op==1) {ledger.remove(a*pg,b*pg);for(auto i=a;i<b;++i)oracle[i]=false;}
    else {
      bool expected=true;
      for(auto i=a;i<b;++i)expected &= oracle[i];
      assert(ledger.covers(a*pg,b*pg)==expected);
    }
    std::uint64_t prev=0;
    for(const auto& r:ledger.ranges()) {
      assert(r.first<r.end);
      assert(prev<=r.first);
      prev=r.end;
    }
  }
  std::puts("LINGSHU185_LEDGER_PROPERTY_20000=PASS_HOST_ONLY");
}
