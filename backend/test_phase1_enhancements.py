#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test script for Phase 1 PDF Improvements - Enhanced Diagram Generation."""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

# Force UTF-8 output on Windows
if sys.stdout.encoding != 'utf-8':
    sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)

from app.models.schemas import AssemblyStep, Part, PartType
from app.services.exploded_view_generator import ExplodedViewSVGGenerator, IsometricProjection


def create_test_parts():
    """Create sample parts for testing."""
    parts = [
        Part(
            id="A1",
            original_index=0,
            part_type=PartType.STRUCTURAL,
            quantity=1,
            volume=500.0,
            dimensions={"width": 100, "height": 20, "depth": 50},
            centroid=[50, 10, 25],
            surface_area=6200.0,
            group_id="structural_frame",
        ),
        Part(
            id="B1",
            original_index=1,
            part_type=PartType.PANEL,
            quantity=1,
            volume=300.0,
            dimensions={"width": 80, "height": 60, "depth": 10},
            centroid=[40, 30, 5],
            surface_area=5200.0,
            group_id="panels",
        ),
        Part(
            id="C1",
            original_index=2,
            part_type=PartType.HARDWARE,
            quantity=4,
            volume=50.0,
            dimensions={"width": 20, "height": 20, "depth": 5},
            centroid=[10, 10, 2.5],
            surface_area=1200.0,
            group_id="brackets",
        ),
    ]
    return parts


def create_test_step():
    """Create a test assembly step."""
    step = AssemblyStep(
        step_number=2,
        title="Install shelf panels",
        description="Attach the shelf panels to the frame structure",
        part_indices=[1, 2],  # B1 and C1
        part_roles={1: "panel", 2: "bracket"},
        context_part_indices=[0],  # A1 already assembled
        duration_minutes=12,
        detail_description="Position the shelf panels horizontally and secure with brackets.",
        assembly_sequence=[
            "Position panels on frame",
            "Align with mounting holes",
            "Insert brackets and tighten",
            "Verify level positioning",
        ],
        warnings=[
            "Do not over-tighten brackets",
            "Ensure panels are level before securing",
        ],
        tips=[
            "Use a level tool for perfect alignment",
            "Tighten in a cross pattern to prevent warping",
        ],
        confidence_score=0.85,
        is_llm_generated=False,
    )
    return step


async def test_isometric_projection():
    """Test IsometricProjection calculations."""
    print("\n=== Testing IsometricProjection ===")

    # Test point projection
    x, y = IsometricProjection.project_point(100, 100, 100)
    print(f"✓ Point projection (100,100,100) -> ({x:.2f}, {y:.2f})")

    # Test box projection
    vertices = IsometricProjection.project_box(0, 0, 0, 100, 50, 30)
    print(f"✓ Box projection: {len(vertices)} vertices calculated")
    for name, (vx, vy) in list(vertices.items())[:3]:
        print(f"  {name}: ({vx:.2f}, {vy:.2f})")

    return True


async def test_exploded_view_generation():
    """Test enhanced exploded view generation."""
    print("\n=== Testing Enhanced Exploded View Generation ===")

    parts = create_test_parts()
    step = create_test_step()

    generator = ExplodedViewSVGGenerator()

    # Generate SVG
    print("Generating enhanced exploded view SVG...")
    svg = await generator.generate_exploded_view(parts, step, total_steps=5)

    # Verify SVG structure
    checks = [
        ("SVG header", "<svg" in svg),
        ("Step progress indicator", "Step 2 of 5" in svg),
        ("Part rendering", "Part A1" in svg and "Part B1" in svg),
        ("Assembly sequence", "Position panels on frame" in svg),
        ("Warnings section", "Do not over-tighten" in svg),
        ("Tips section", "Tips" in svg or "level tool" in svg),
        ("Difficulty badge", "duration-badge" in svg),
        ("Active parts class", "part-active" in svg),
        ("Context parts class", "part-context" in svg),
        ("Assembly flow", "assembly-flow" in svg),
    ]

    for check_name, result in checks:
        status = "✓" if result else "✗"
        print(f"{status} {check_name}")

    if not all(result for _, result in checks):
        print("\n❌ Some checks failed!")
        print(f"\nGenerated SVG (first 500 chars):\n{svg[:500]}...")
        return False

    print(f"\n✓ SVG generated successfully ({len(svg)} bytes)")
    return True


async def test_canvas_sizing():
    """Test optimal canvas sizing."""
    print("\n=== Testing Optimal Canvas Sizing ===")

    parts = create_test_parts()
    step = create_test_step()

    generator = ExplodedViewSVGGenerator()

    # Test with different step configurations
    canvas_w, canvas_h = generator._calculate_optimal_canvas(parts, step)
    print(f"✓ Canvas size: {canvas_w:.0f} × {canvas_h:.0f} pixels")

    # Verify size is within expected ranges
    if 600 <= canvas_w <= 1400 and 500 <= canvas_h <= 1800:
        print("✓ Canvas dimensions are within expected ranges")
        return True
    else:
        print(f"❌ Canvas dimensions out of range: {canvas_w} × {canvas_h}")
        return False


async def test_color_adjustments():
    """Test color adjustment methods."""
    print("\n=== Testing Color Adjustment Methods ===")

    generator = ExplodedViewSVGGenerator()

    # Test lighten color
    original = "#4a90e2"
    lightened = generator._lighten_color(original, 0.3)
    print(f"✓ Original: {original} -> Lightened: {lightened}")

    # Test brightness adjustment
    darkened = generator._adjust_color_brightness(original, 0.7)
    print(f"✓ Original: {original} -> Darkened (0.7): {darkened}")

    brightened = generator._adjust_color_brightness(original, 1.2)
    print(f"✓ Original: {original} -> Brightened (1.2): {brightened}")

    return True


async def main():
    """Run all tests."""
    print("=" * 60)
    print("Phase 1 PDF Improvements - Enhanced Diagram Generation Tests")
    print("=" * 60)

    tests = [
        ("IsometricProjection", test_isometric_projection),
        ("Color Adjustments", test_color_adjustments),
        ("Canvas Sizing", test_canvas_sizing),
        ("Exploded View Generation", test_exploded_view_generation),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ {test_name} failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All Phase 1 enhancement tests passed!")
        return 0
    else:
        print(f"\n❌ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
