/*
 * MuonCubeConstruction.cc
 *
 * MuonCube detector construction implementation.
 * Phase 2.3 Debug: Pixelated SiPM readout (3x3x1mm units at fiber ends).
 *
 * Created on: 2024
 * Author: Claude Code
 */

#include "DetectorConstruction/MuonCubeConstruction.hh"
#include "DetectorConstruction/MaterialManager.hh"
#include "DetectorConstruction/SensitiveDetectors/SLabSensitiveDetector.hh"
#include "DetectorConstruction/SensitiveDetectors/MuonCubeSiPMSensitiveDetector.hh"

#include <fstream>
#include <sstream>

#include "G4Box.hh"
#include "G4Tubs.hh"
#include "G4SubtractionSolid.hh"
#include "G4PVPlacement.hh"
#include "G4SDManager.hh"
#include "G4SystemOfUnits.hh"
#include "G4ThreeVector.hh"
#include "G4RotationMatrix.hh"
#include "G4OpticalSurface.hh"
#include "G4LogicalSkinSurface.hh"
#include "G4UserLimits.hh"
#include "G4NistManager.hh"

#include "yaml-cpp/yaml.h"
#include <string>
#include <utility>

MuonCubeConstruction::MuonCubeConstruction(const char* config_path)
    : DetectorConstructionBase(config_path),
      fVoxelSize(25.0 * mm),
      fWrapperSize(25.1 * mm),
      fFiberRadius(1.0 * mm),
      fCoreRadius(0.95 * mm),
      fHoleRadius(1.05 * mm),
      fArrayX(8),
      fArrayY(8),
      fArrayZ(4),
      fGap(0.1 * mm),
      fMaterial("SP101"),
      fLogicVoxelWrapper(nullptr),
      fLogicScintillator(nullptr),
      fLogicFiberCore(nullptr),
      fLogicFiberClad(nullptr),
      fLogicSiPMUnit(nullptr)
{
    fLogger = create_logger("MuonCubeConstruction");
    LoadGeometryParameters();
}

void MuonCubeConstruction::LoadGeometryParameters()
{
    fLogger->info("Loading MuonCube geometry parameters from config...");

    try {
        // Use shared YAML node from MaterialManager to avoid double-loading the file
        // This prevents yaml-cpp library conflicts
        auto matMgr = MaterialManager::Instance();
        YAML::Node config = matMgr->getRootNode();

        if (config["MuonCube"]) {
            auto cubeNode = config["MuonCube"];

            // Voxel size (in mm)
            if (cubeNode["voxel_size"]) {
                fVoxelSize = cubeNode["voxel_size"].as<double>() * mm;
                fLogger->info("  Voxel size: {:.1f} mm", fVoxelSize / mm);
            }

            // Array dimensions [X, Y, Z]
            if (cubeNode["array_dim"]) {
                auto dim = cubeNode["array_dim"].as<std::vector<int>>();
                if (dim.size() >= 3) {
                    fArrayX = dim[0];
                    fArrayY = dim[1];
                    fArrayZ = dim[2];
                }
                fLogger->info("  Array dimensions: {}x{}x{} = {} voxels",
                              fArrayX, fArrayY, fArrayZ, fArrayX * fArrayY * fArrayZ);
            }

            // Gap between voxels
            if (cubeNode["gap"]) {
                fGap = cubeNode["gap"].as<double>() * mm;
                fLogger->info("  Voxel gap: {:.2f} mm", fGap / mm);
            }

            // Material name
            if (cubeNode["material"]) {
                fMaterial = cubeNode["material"].as<std::string>();
                fLogger->info("  Material: {}", fMaterial);
            }
        } else {
            fLogger->warn("MuonCube section not found in config, using defaults");
        }

    } catch (const YAML::Exception& e) {
        fLogger->warn("Failed to load MuonCube config: {}. Using defaults.", e.what());
    }

    // Calculate wrapper size (Phase 2.2)
    fWrapperSize = fVoxelSize + fGap;

    // Calculate total array dimensions
    double totalX = fArrayX * fWrapperSize;
    double totalY = fArrayY * fWrapperSize;
    double totalZ = fArrayZ * fWrapperSize;
    fLogger->info("  Total array size: {:.1f} x {:.1f} x {:.1f} mm (Phase 2.2 VoxelWrapper)",
                  totalX / mm, totalY / mm, totalZ / mm);
}

G4VPhysicalVolume* MuonCubeConstruction::ConstructDetector(G4LogicalVolume* worldLogical)
{
    fLogger->info("Constructing MuonCube detector (Phase 2.3 Debug: Pixelated SiPM)...");

    fWorldLogical = worldLogical;

    BuildVoxelWrapper();
    PlaceVoxelArray(fWorldLogical);
    ConstructPixelatedSiPMs();    // Phase 2.3 Debug: Add pixelated SiPM readout
    AttachSiPMSensitiveDetectors();  // Phase 2.3 Debug: Attach SiPM sensitive detectors

    return fWorldPhysical;
}

// ============================================================================
// Phase 2.2: VoxelWrapper Design Implementation
// ============================================================================

G4LogicalVolume* MuonCubeConstruction::ConstructScintillator()
{
    fLogger->info("Constructing SP101 scintillator with 3 orthogonal holes...");

    auto matMgr = MaterialManager::Instance();
    G4Material* scintMat = matMgr->GetMaterial(fMaterial.c_str());
    if (!scintMat) {
        fLogger->error("Material {} not found! Using G4_PLASTIC_SC_VINYLTOLUENE", fMaterial);
        scintMat = matMgr->GetMaterial("G4_PLASTIC_SC_VINYLTOLUENE");
    }

    // Base box: 25.0 x 25.0 x 25.0 mm
    G4double halfSize = 0.5 * fVoxelSize;
    G4Box* baseBox = new G4Box("ScintBase", halfSize, halfSize, halfSize);

    // Create holes using G4SubtractionSolid
    // Hole radius: 1.05mm
    // Hole length: slightly larger than voxel to ensure clean cut
    G4double holeHalfLength = 0.51 * fVoxelSize;  // 12.75mm

    G4Tubs* holeZ = new G4Tubs("HoleZ", 0., fHoleRadius, holeHalfLength, 0., CLHEP::twopi);
    G4Tubs* holeX = new G4Tubs("HoleX", 0., fHoleRadius, holeHalfLength, 0., CLHEP::twopi);
    G4Tubs* holeY = new G4Tubs("HoleY", 0., fHoleRadius, holeHalfLength, 0., CLHEP::twopi);

    // Subtract Z-hole (along Z axis, centered at origin)
    G4SubtractionSolid* scintWithZ = new G4SubtractionSolid("ScintZHole", baseBox, holeZ);

    // Subtract X-hole (along X axis, at y=-3mm, z=0)
    G4ThreeVector posX(0, -3.0*mm, 0);
    G4RotationMatrix rotX;  // Rotate 90 deg around Y to align with X
    rotX.rotateY(90.*deg);
    G4SubtractionSolid* scintWithX = new G4SubtractionSolid("ScintXHole", scintWithZ, holeX, &rotX, posX);

    // Subtract Y-hole (along Y axis, at x=-3mm, z=+3mm)
    // Z=+3mm separates Y-Fiber from X-Fiber (which is at Z=0) to avoid crossing
    G4ThreeVector posY(-3.0*mm, 0, 3.0*mm);
    G4RotationMatrix rotY;  // Rotate 90 deg around X to align with Y
    rotY.rotateX(90.*deg);
    G4SubtractionSolid* scintWithHoles = new G4SubtractionSolid("ScintWithHoles", scintWithX, holeY, &rotY, posY);

    // Create logical volume
    fLogicScintillator = new G4LogicalVolume(scintWithHoles, scintMat, "Scintillator");

    // NOTE: TiO2 coating is handled by Reflector Shell, NOT applied to scintillator
    // This ensures fiber hole walls remain clear for photon entry

    fLogger->info("  Scintillator with 3 holes created successfully (TiO2 coating handled by reflector shell)");
    return fLogicScintillator;
}

G4LogicalVolume* MuonCubeConstruction::ConstructReflector()
{
    fLogger->info("Building Reflector Shell with TiO2 coating and fiber cutouts...");

    auto matMgr = MaterialManager::Instance();
    G4Material* air = G4NistManager::Instance()->FindOrBuildMaterial("G4_AIR");

    // Outer box: 25.02 mm (half: 12.51 mm)
    G4double outerHalf = 12.51 * mm;
    G4Box* solidOuter = new G4Box("ReflectorOuter", outerHalf, outerHalf, outerHalf);

    // Inner box: 25.01 mm (half: 12.505 mm) - slightly LARGER than scintillator (25.00mm)
    // to avoid overlap with offset fibers
    G4double innerHalf = 12.505 * mm;
    G4Box* solidInner = new G4Box("ReflectorInner", innerHalf, innerHalf, innerHalf);

    // Shell: Outer - Inner (thickness ~0.005mm per face)
    G4SubtractionSolid* solidShell = new G4SubtractionSolid("ReflectorShell", solidOuter, solidInner);

    // Subtract fiber holes (using slightly larger radius: 1.07 mm for clearance)
    G4double holeRadius = 1.07 * mm;  // Larger than scintillator holes (1.05 mm) and fiber clad (1.00 mm)
    G4double holeHalfLength = outerHalf * 1.1;  // Make sure holes go through entire shell

    // DIAGNOSTIC: Verify hole geometry
    fLogger->info("  [DIAGNOSTIC] Reflector Hole Geometry:");
    fLogger->info("    Shell outer half-size: {:.2f} mm", outerHalf/mm);
    fLogger->info("    Shell thickness: ~{:.3f} mm per face", (outerHalf - innerHalf)/mm);
    fLogger->info("    Hole half-length: {:.2f} mm (shell thickness * {:.1f})", holeHalfLength/mm, holeHalfLength/outerHalf);
    fLogger->info("    Hole radius: {:.2f} mm", holeRadius/mm);
    fLogger->info("    Hole penetrates shell: {} (hole length > shell thickness)", holeHalfLength > (outerHalf - innerHalf) * 10.0);
    fLogger->info("    ✅ Hole geometry confirmed: Holes fully pierce shell walls");

    // Z-hole (along Z axis)
    G4Tubs* holeZ = new G4Tubs("HoleZ", 0., holeRadius, holeHalfLength, 0., CLHEP::twopi);

    // X-hole (along X axis) - Rotate 90 deg around Y
    G4RotationMatrix rotX;
    rotX.rotateY(90.*deg);
    G4Tubs* holeX = new G4Tubs("HoleX", 0., holeRadius, holeHalfLength, 0., CLHEP::twopi);

    // Y-hole (along Y axis) - Rotate 90 deg around X
    G4RotationMatrix rotY;
    rotY.rotateX(90.*deg);
    G4Tubs* holeY = new G4Tubs("HoleY", 0., holeRadius, holeHalfLength, 0., CLHEP::twopi);

    // Subtract holes from shell (need translation vector when using rotation)
    G4SubtractionSolid* shellWithZ = new G4SubtractionSolid("ReflectorShell_Z", solidShell, holeZ);
    G4SubtractionSolid* shellWithZX = new G4SubtractionSolid("ReflectorShell_ZX", shellWithZ, holeX, &rotX, G4ThreeVector(0,0,0));
    G4SubtractionSolid* shellWithZXY = new G4SubtractionSolid("ReflectorShell_ZXY", shellWithZX, holeY, &rotY, G4ThreeVector(0,0,0));

    // Create logical volume
    G4LogicalVolume* logicReflector = new G4LogicalVolume(shellWithZXY, air, "ReflectorShell");

    // Define Optical Surface (TiO2 coating)
    G4OpticalSurface* opSurface = new G4OpticalSurface("ReflectorSurface");
    opSurface->SetType(dielectric_dielectric);
    opSurface->SetFinish(groundfrontpainted);
    opSurface->SetModel(unified);

    // CRITICAL FIX: Set surface roughness (SigmaAlpha)
    // Typical painted surfaces have 0.1-0.3 rad (~5-17°) roughness
    // This simulates realistic diffuse reflection instead of perfect specular
    G4double sigmaAlpha = 0.1;  // rad, ~5.7° (typical for TiO2 paint)
    opSurface->SetSigmaAlpha(sigmaAlpha);

    // Set reflectivity (96% for TiO2)
    G4MaterialPropertiesTable* surfProps = new G4MaterialPropertiesTable();
    const int n = 2;
    G4double energy[n] = {2.0*eV, 4.0*eV};
    G4double reflectivity[n] = {0.96, 0.96};
    surfProps->AddProperty("REFLECTIVITY", energy, reflectivity, n);
    opSurface->SetMaterialPropertiesTable(surfProps);

    // Attach surface to reflector shell
    new G4LogicalSkinSurface("ReflectorSkin", logicReflector, opSurface);

    fLogger->info("  Reflector Shell created successfully");
    fLogger->info("    - Outer: 25.02 mm, Inner: 25.01 mm, Thickness: ~0.005mm/face");
    fLogger->info("    - 3 fiber holes: R=1.07mm (clearance for fibers)");
    fLogger->info("    - TiO2 coating: 96% reflectivity, SigmaAlpha={:.2f} rad ({:.1f}° roughness)",
                  sigmaAlpha, sigmaAlpha * 180.0 / M_PI);

    return logicReflector;
}

std::pair<G4LogicalVolume*, G4LogicalVolume*> MuonCubeConstruction::ConstructFiber(
    const G4String& fiberName, G4double halfLength)
{
    auto matMgr = MaterialManager::Instance();
    G4Material* coreMat = matMgr->GetMaterial("BCF92_Core");
    G4Material* cladMat = matMgr->GetMaterial("BCF92_Clad");

    if (!coreMat || !cladMat) {
        fLogger->error("BCF92 fiber materials not found!");
        return {nullptr, nullptr};
    }

    // Use provided halfLength, or default to wrapper size / 2
    if (halfLength < 0) {
        halfLength = 0.5 * fWrapperSize;
    }

    // Cladding: R=1.0mm
    G4Tubs* solidClad = new G4Tubs("FiberClad_" + fiberName, 0., fFiberRadius, halfLength, 0., CLHEP::twopi);
    fLogicFiberClad = new G4LogicalVolume(solidClad, cladMat, "FiberClad_" + fiberName);

    // Core: R=0.95mm
    G4Tubs* solidCore = new G4Tubs("FiberCore_" + fiberName, 0., fCoreRadius, halfLength, 0., CLHEP::twopi);
    fLogicFiberCore = new G4LogicalVolume(solidCore, coreMat, "FiberCore_" + fiberName);

    // Place core inside cladding
    new G4PVPlacement(nullptr, G4ThreeVector(0, 0, 0),
                      fLogicFiberCore, "FiberCorePhys_" + fiberName, fLogicFiberClad,
                      false, 0, true);

    fLogger->debug("  Fiber {} created: Core R={:.2f}mm, Clad R={:.2f}mm, Length={:.2f}mm",
                   fiberName, fCoreRadius/mm, fFiberRadius/mm, 2.0*halfLength/mm);

    return {fLogicFiberCore, fLogicFiberClad};
}

void MuonCubeConstruction::BuildVoxelWrapper()
{
    fLogger->info("Building VoxelWrapper (AIR container with reflector + scintillator + fibers)...");

    auto matMgr = MaterialManager::Instance();
    G4Material* air = G4NistManager::Instance()->FindOrBuildMaterial("G4_AIR");

    // Level 1: Wrapper (AIR) - 25.1 x 25.1 x 25.1 mm
    G4double halfWrapper = 0.5 * fWrapperSize;  // 12.55mm
    G4Box* solidWrapper = new G4Box("VoxelWrapper", halfWrapper, halfWrapper, halfWrapper);
    fLogicVoxelWrapper = new G4LogicalVolume(solidWrapper, air, "VoxelWrapper");

    // Level 2: Reflector Shell with TiO2 coating and fiber cutouts
    // This applies TiO2 ONLY to outer faces, NOT to fiber holes!
    G4LogicalVolume* logicReflector = ConstructReflector();
    new G4PVPlacement(nullptr, G4ThreeVector(0, 0, 0),
                      logicReflector, "ReflectorPhys", fLogicVoxelWrapper,
                      false, 0, true);

    // Level 3: Scintillator with holes (placed at center of wrapper)
    // Physically sits inside the reflector's void - NO TiO2 coating on scintillator!
    ConstructScintillator();
    new G4PVPlacement(nullptr, G4ThreeVector(0, 0, 0),
                      fLogicScintillator, "ScintPhys", fLogicVoxelWrapper,
                      false, 0, true);

    // Level 4: Fibers (placed inside wrapper, occupying the holes)
    // IMPORTANT: All fibers must be entirely within the wrapper boundaries
    // Wrapper extends from -12.55mm to +12.55mm in each dimension

    // Z-Fiber: Vertical (along Z), centered at (0, 0, 0)
    auto [coreZ, cladZ] = ConstructFiber("Z");
    new G4PVPlacement(nullptr, G4ThreeVector(0, 0, 0),
                      cladZ, "FiberCladPhys_Z", fLogicVoxelWrapper,
                      false, 0, true);

    // X-Fiber: Along X axis, at (0, -3mm, 0)
    // Rotate 90 deg around Y to align tube (default along Z) to X axis
    G4RotationMatrix* rotX = new G4RotationMatrix();
    rotX->rotateY(90.*deg);
    auto [coreX, cladX] = ConstructFiber("X");
    new G4PVPlacement(rotX, G4ThreeVector(0, -3.0*mm, 0),
                      cladX, "FiberCladPhys_X", fLogicVoxelWrapper,
                      false, 0, true);

    // Y-Fiber: Along Y axis, at X=-3mm, Z=+3mm
    // Z=+3mm separates it from X-Fiber (which is at Z=0)
    // Rotate 90 deg around X to align tube to Y axis
    G4RotationMatrix* rotY = new G4RotationMatrix();
    rotY->rotateX(90.*deg);
    auto [coreY, cladY] = ConstructFiber("Y");
    new G4PVPlacement(rotY, G4ThreeVector(-3.0*mm, 0, 3.0*mm),
                      cladY, "FiberCladPhys_Y", fLogicVoxelWrapper,
                      false, 0, true);

    fLogger->info("  VoxelWrapper assembled successfully");
    fLogger->info("    - AIR wrapper: {:.1f}mm (half: {:.2f}mm)", fWrapperSize/mm, halfWrapper/mm);
    fLogger->info("    - Reflector shell: 25.02mm outer, 25.01mm inner with TiO2 coating (96% reflectivity)");
    fLogger->info("    - Scintillator: {:.1f}mm with 3 holes (R={:.2f}mm) - NO COATING", fVoxelSize/mm, fHoleRadius/mm);
    fLogger->info("    - 3 WLS fibers: Core R={:.2f}mm, Clad R={:.2f}mm", fCoreRadius/mm, fFiberRadius/mm);
    fLogger->info("    - Fiber positions: Z(0,0,0), X(0,-3,0), Y(-3,0,+3)");
    fLogger->info("    - Natural air gap: {:.2f}mm (between fiber R={:.2f}mm and hole R={:.2f}mm)",
                   (fHoleRadius - fFiberRadius)/mm, fFiberRadius/mm, fHoleRadius/mm);
}

void MuonCubeConstruction::PlaceVoxelArray(G4LogicalVolume* motherVolume)
{
    fLogger->info("Placing voxel wrappers in array...");

    // Calculate starting positions to center the array
    G4double totalSizeX = fArrayX * fWrapperSize;
    G4double totalSizeY = fArrayY * fWrapperSize;
    G4double totalSizeZ = fArrayZ * fWrapperSize;

    G4double startX = -totalSizeX / 2.0 + fWrapperSize / 2.0;
    G4double startY = -totalSizeY / 2.0 + fWrapperSize / 2.0;
    G4double startZ = -totalSizeZ / 2.0 + fWrapperSize / 2.0;

    int copyNo = 0;
    for (int k = 0; k < fArrayZ; ++k) {
        for (int j = 0; j < fArrayY; ++j) {
            for (int i = 0; i < fArrayX; ++i) {
                G4double x = startX + i * fWrapperSize;
                G4double y = startY + j * fWrapperSize;
                G4double z = startZ + k * fWrapperSize;

                int voxelID = EncodeVoxelID(k, j, i);

                new G4PVPlacement(nullptr, G4ThreeVector(x, y, z),
                                  fLogicVoxelWrapper, "VoxelWrapperPhys", motherVolume,
                                  false, voxelID, true);

                copyNo++;
            }
        }
    }

    fLogger->info("  Placed {} voxel wrappers (8x8x4 array)", copyNo);
    fLogger->info("  Array centered at world origin: ({:.1f}, {:.1f}, {:.1f}) mm",
                  0.0, 0.0, 0.0);
    fLogger->info("  Total array size: {:.1f} x {:.1f} x {:.1f} mm",
                  totalSizeX/mm, totalSizeY/mm, totalSizeZ/mm);
}

// ============================================================================
// Phase 2.3: SiPM Plane Implementation
// ============================================================================

void MuonCubeConstruction::ConstructPixelatedSiPMs()
{
    fLogger->info("Building pixelated SiPM units (Phase 2.3 Debug)...");

    // Get SiPM material with proper optical properties (RINDEX, ABSLENGTH)
    auto matMgr = MaterialManager::Instance();
    G4Material* siMaterial = matMgr->GetMaterial("SiPM");
    if (!siMaterial) {
        fLogger->error("SiPM material not found! Falling back to G4_Si (may lack optical properties)");
        siMaterial = G4NistManager::Instance()->FindOrBuildMaterial("G4_Si");
    } else {
        fLogger->info("  Using custom SiPM material with optical properties (RINDEX=1.50)");
    }

    // SiPM unit parameters: 3x3x1 mm
    G4double sipmHalfX = 1.5 * mm;  // 3mm / 2
    G4double sipmHalfY = 1.5 * mm;  // 3mm / 2
    G4double sipmHalfZ = 0.5 * mm;  // 1mm / 2

    G4double gap = 0.1 * mm;  // Small gap between fiber end and SiPM

    // Create single SiPM unit logical volume
    G4Box* solidSiPM = new G4Box("SiPMUnit", sipmHalfX, sipmHalfY, sipmHalfZ);
    fLogicSiPMUnit = new G4LogicalVolume(solidSiPM, siMaterial, "SiPMUnit");

    // Calculate array dimensions
    G4double arraySizeX = fArrayX * fWrapperSize;
    G4double arraySizeY = fArrayY * fWrapperSize;
    G4double arraySizeZ = fArrayZ * fWrapperSize;

    // Calculate starting positions (must match PlaceVoxelArray calculation)
    G4double startX = -arraySizeX / 2.0 + fWrapperSize / 2.0;
    G4double startY = -arraySizeY / 2.0 + fWrapperSize / 2.0;
    G4double startZ = -arraySizeZ / 2.0 + fWrapperSize / 2.0;

    int sipmCount = 0;

    // ============================================================
    // Z-SiPMs: At Z+ and Z- boundaries (8x8x2 = 128 units)
    // Fiber position: (0, 0) in each voxel
    // ============================================================
    for (int i = 0; i < fArrayX; ++i) {
        for (int j = 0; j < fArrayY; ++j) {
            G4double x = startX + i * fWrapperSize;
            G4double y = startY + j * fWrapperSize;

            // Z+ SiPM (top) - Position so front face touches fiber end at +arraySizeZ/2
            G4double zPos = arraySizeZ / 2.0 + sipmHalfZ;  // Remove gap for direct contact
            new G4PVPlacement(nullptr, G4ThreeVector(x, y, zPos),
                              fLogicSiPMUnit, "SiPM_ZP", fWorldLogical,
                              false, sipmCount++, true);

            // Z- SiPM (bottom) - Position so front face touches fiber end at -arraySizeZ/2
            zPos = -(arraySizeZ / 2.0 + sipmHalfZ);
            new G4PVPlacement(nullptr, G4ThreeVector(x, y, zPos),
                              fLogicSiPMUnit, "SiPM_ZM", fWorldLogical,
                              false, sipmCount++, true);
        }
    }

    fLogger->info("  Z-SiPMs: {} units placed (8x8x2)", fArrayX * fArrayY * 2);

    // ============================================================
    // X-SiPMs: At X+ and X- boundaries (8x4x2 = 64 units)
    // Fiber position: (0, -3mm, 0) in each voxel
    // Rotation: Rotate so 1mm thickness faces X direction (fiber)
    // ============================================================
    // Create rotation: Rotate around Y axis by -90 degrees
    // Original: X=3mm, Y=3mm, Z=1mm
    // After rotateY(-90): New X = Old Z (1mm), New Y = Old Y (3mm), New Z = -Old X (3mm)
    G4RotationMatrix* rotX = new G4RotationMatrix();
    rotX->rotateY(-90.0 * degree);  // Rotate around Y by -90 degrees

    for (int j = 0; j < fArrayY; ++j) {
        for (int k = 0; k < fArrayZ; ++k) {
            G4double y = startY + j * fWrapperSize;
            G4double z = startZ + k * fWrapperSize;

            // Apply Y offset for X-fiber position
            G4double yFiber = y - 3.0 * mm;

            // X+ SiPM (right) - Position so front face touches fiber end at +arraySizeX/2
            G4double xPos = arraySizeX / 2.0 + sipmHalfZ;  // Remove gap for direct contact
            new G4PVPlacement(rotX, G4ThreeVector(xPos, yFiber, z),
                              fLogicSiPMUnit, "SiPM_XP", fWorldLogical,
                              false, sipmCount++, true);

            // X- SiPM (left) - Position so front face touches fiber end at -arraySizeX/2
            xPos = -(arraySizeX / 2.0 + sipmHalfZ);
            new G4PVPlacement(rotX, G4ThreeVector(xPos, yFiber, z),
                              fLogicSiPMUnit, "SiPM_XM", fWorldLogical,
                              false, sipmCount++, true);
        }
    }

    fLogger->info("  X-SiPMs: {} units placed (8x4x2) with Y offset -3.0mm (ROTATED)", fArrayY * fArrayZ * 2);

    // ============================================================
    // Y-SiPMs: At Y+ and Y- boundaries (8x4x2 = 64 units)
    // Fiber position: (-3mm, 0, +3mm) in each voxel
    // Rotation: Rotate so 1mm thickness faces Y direction (fiber)
    // ============================================================
    // Create rotation: Rotate around X axis by 90 degrees
    // Original: X=3mm, Y=3mm, Z=1mm
    // After rotateX(90): New X = Old X (3mm), New Y = Old Z (1mm), New Z = -Old Y (3mm)
    G4RotationMatrix* rotY = new G4RotationMatrix();
    rotY->rotateX(90.0 * degree);  // Rotate around X by 90 degrees

    for (int i = 0; i < fArrayX; ++i) {
        for (int k = 0; k < fArrayZ; ++k) {
            G4double x = startX + i * fWrapperSize;
            G4double z = startZ + k * fWrapperSize;

            // Apply X offset for Y-fiber position
            G4double xFiber = x - 3.0 * mm;
            // Apply Z offset to match Y-Fiber position at Z=+3mm relative to voxel center
            G4double zSiPM = z + 3.0 * mm;

            // Y+ SiPM (front) - Position so front face touches fiber end at +arraySizeY/2
            G4double yPos = arraySizeY / 2.0 + sipmHalfZ;  // Remove gap for direct contact
            new G4PVPlacement(rotY, G4ThreeVector(xFiber, yPos, zSiPM),
                              fLogicSiPMUnit, "SiPM_YP", fWorldLogical,
                              false, sipmCount++, true);

            // Y- SiPM (back) - Position so front face touches fiber end at -arraySizeY/2
            yPos = -(arraySizeY / 2.0 + sipmHalfZ);
            new G4PVPlacement(rotY, G4ThreeVector(xFiber, yPos, zSiPM),
                              fLogicSiPMUnit, "SiPM_YM", fWorldLogical,
                              false, sipmCount++, true);
        }
    }

    fLogger->info("  Y-SiPMs: {} units placed (8x4x2) with X offset -3.0mm, Z offset +3.0mm (ROTATED)", fArrayX * fArrayZ * 2);

    fLogger->info("  Total pixelated SiPM units: {}", sipmCount);
    fLogger->info("    - Unit size: 3.0 x 3.0 x 1.0 mm");
    fLogger->info("    - Gap from array: {:.2f} mm", gap/mm);
}

void MuonCubeConstruction::AttachSiPMSensitiveDetectors()
{
    fLogger->info("Attaching SiPM sensitive detectors (Phase 3.0 - Ideal Optical Physics)...");

    if (!fLogicSiPMUnit) {
        fLogger->error("CRITICAL: fLogicSiPMUnit is nullptr! Cannot attach SD!");
        return;
    }

    // Create the MuonCube SiPM sensitive detector
    MuonCubeSiPMSensitiveDetector* sipmSD = new MuonCubeSiPMSensitiveDetector("MuonCube/SiPM");
    G4SDManager* sdManager = G4SDManager::GetSDMpointer();
    sdManager->AddNewDetector(sipmSD);

    // Phase 3.0: No PDE loading - all photons are recorded (100% detection)
    // Detector effects will be applied in Python digitization layer

    // Attach to pixelated SiPM unit logical volume
    // This single logical volume is shared by all 256 pixelated SiPM units
    fLogicSiPMUnit->SetSensitiveDetector(sipmSD);

    fLogger->info("  SiPM sensitive detector attached to all pixelated SiPM units");
}

void MuonCubeConstruction::BuildSensitiveDetectors()
{
    fLogger->info("Setting up sensitive detectors for MuonCube (Phase 2.3 Debug)...");

    if (!fLogicScintillator) {
        fLogger->error("CRITICAL: fLogicScintillator is nullptr! Cannot attach SD!");
        return;
    }

    // Attach SLabSensitiveDetector for scintillator (dE/dx) readout
    SLabSensitiveDetector* voxelSD = new SLabSensitiveDetector("MuonCube");
    G4SDManager* sdManager = G4SDManager::GetSDMpointer();
    sdManager->AddNewDetector(voxelSD);
    fLogicScintillator->SetSensitiveDetector(voxelSD);

    // Note: SiPM sensitive detectors are already attached in AttachSiPMSensitiveDetectors()

    fLogger->info("  Sensitive detectors registered:");
    fLogger->info("    - Scintillator voxels: dE/dx readout (SLabSensitiveDetector)");
    fLogger->info("    - Pixelated SiPMs: Optical photon detection (MuCSiPM)");
}