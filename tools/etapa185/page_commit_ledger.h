// Lingshu 185 — pure bookkeeping for pages whose PROT_READ|PROT_WRITE
// mprotect() actually succeeded. Independent of PS4 SDK and game bytes.
#pragma once
#include <algorithm>
#include <cstdint>
#include <vector>

namespace lingshu185 {
struct Range { std::uint64_t first, end; };

class CommitLedger {
    std::vector<Range> spans_; // sorted, coalesced half-open intervals
public:
    const std::vector<Range>& ranges() const { return spans_; }

    bool covers(std::uint64_t first, std::uint64_t end) const {
        if (first >= end) return false;
        std::uint64_t cursor = first;
        for (const auto& r : spans_) {
            if (r.end <= cursor) continue;
            if (r.first > cursor) return false;
            cursor = std::max(cursor, r.end);
            if (cursor >= end) return true;
        }
        return false;
    }

    void add(std::uint64_t first, std::uint64_t end) {
        if (first >= end) return;
        Range inserted{first,end};
        std::vector<Range> next;
        next.reserve(spans_.size()+1);
        bool placed = false;
        for (const auto& r : spans_) {
            if (r.end < inserted.first) next.push_back(r);
            else if (inserted.end < r.first) {
                if (!placed) { next.push_back(inserted); placed=true; }
                next.push_back(r);
            } else {
                inserted.first=std::min(inserted.first,r.first);
                inserted.end=std::max(inserted.end,r.end);
            }
        }
        if (!placed) next.push_back(inserted);
        spans_.swap(next);
    }

    void remove(std::uint64_t first, std::uint64_t end) {
        if (first >= end) return;
        std::vector<Range> next;
        next.reserve(spans_.size()+1);
        for (const auto& r : spans_) {
            if (end <= r.first || first >= r.end) { next.push_back(r); continue; }
            if (r.first < first) next.push_back({r.first,first});
            if (r.end > end) next.push_back({end,r.end});
        }
        spans_.swap(next);
    }
};
}
