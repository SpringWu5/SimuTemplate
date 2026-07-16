/*
 * MuonCubeSiPMSensitiveDetector.cc
 *
 * Implementation of MuonCube SiPM sensitive detector
 *
 * Phase 3.0: Ideal optical physics - records 100% of arriving photons
 * Phase 3.0: ML-optimized slim SiPM hits
 *
 * Created on: 2024
 * Author: Claude Code
 */

#include "DetectorConstruction/SensitiveDetectors/MuonCubeSiPMSensitiveDetector.hh"
#include "Record/OutputManager.hh"
#include "Record/SiPMHit.hh"

#include "G4Step.hh"
#include "G4TouchableHistory.hh"
#include "G4Track.hh"
#include "G4VTouchable.hh"
#include "G4OpticalPhoton.hh"
#include "G4SystemOfUnits.hh"
#include "G4PhysicalConstants.hh"
#include "G4VProcess.hh"
#include "G4RunManager.hh"
#include "spdlog/spdlog.h"
#include <algorithm>
#include <cmath>

MuonCubeSiPMSensitiveDetector::MuonCubeSiPMSensitiveDetector(const G4String& name)
    : G4VSensitiveDetector(name),
      fTotalOpticalHits(0),
      fTotalWLPHits(0)
{
    // Collection name for hits
    collectionName.insert("MuCSiPMHitsCollection");
}

MuonCubeSiPMSensitiveDetector::~MuonCubeSiPMSensitiveDetector()
{
}

void MuonCubeSiPMSensitiveDetector::Initialize(G4HCofThisEvent*)
{
    fTotalOpticalHits = 0;
    fTotalWLPHits = 0;
}

G4bool MuonCubeSiPMSensitiveDetector::ProcessHits(G4Step* step, G4TouchableHistory*)
{
    // Only process optical photons
    G4Track* track = step->GetTrack();
    if (track->GetDefinition() != G4OpticalPhoton::OpticalPhotonDefinition()) {
        return false;
    }

    fTotalOpticalHits++;

    // Get hit information
    G4StepPoint* postStep = step->GetPostStepPoint();
    G4ThreeVector pos = postStep->GetPosition();
    G4double energy = postStep->GetKineticEnergy();
    G4double hitTime = postStep->GetGlobalTime() / ns;

    // ================================================================
    // PHASE 2.6: POSITION-BASED DETECTION (Most Reliable)
    // ================================================================
    // Instead of relying on copy numbers which can be confusing due
    // to volume hierarchy, we directly calculate fiber ID from position.
    // This is the MOST RELIABLE method!
    // ================================================================

    G4int fiberID = -1;

    // Get volume name to determine which SiPM plane we're on
    G4TouchableHandle touchable = postStep->GetTouchableHandle();
    G4String volName = "unknown";
    if (touchable) {
        G4VPhysicalVolume* physVol = touchable->GetVolume();
        if (physVol) {
            volName = physVol->GetName();
        }
    }

    // ================================================================
    // PHASE 3.0: DUAL-ENDED READOUT ENCODING (End-Bit Schema)
    // ================================================================
    // Distinguish between Plus and Minus ends by adding +1000 offset
    // for positive ends. This enables attenuation correction and
    // time-difference-of-arrival position reconstruction.
    // ================================================================

    // Calculate fiber ID directly from hit position
    if (volName.contains("SiPM_Z")) {
        // Z-SiPM: Use X and Y position to determine row and col
        G4double x = pos.x() / mm;
        G4double y = pos.y() / mm;
        G4double z = pos.z() / mm;

        // Calculate row and col from position (must match construction formulas)
        // Construction: x = startX + col * wrapperSize = -87.85 + col * 25.1
        //             y = startY + row * wrapperSize = -87.85 + row * 25.1
        // Therefore: col = (x + 87.85) / 25.1
        //            row = (y + 87.85) / 25.1

        G4int col = static_cast<G4int>(std::round((x + 87.85) / 25.1));
        G4int row = static_cast<G4int>(std::round((y + 87.85) / 25.1));

        // Clamp to valid range
        col = std::max(0, std::min(7, col));
        row = std::max(0, std::min(7, row));

        // Phase 3.0: Add end-bit to distinguish ZP (top) from ZM (bottom)
        // Base ID: 10000 + row*100 + col
        // If z > 0 (ZP, top end): add 1000
        // If z < 0 (ZM, bottom end): no offset
        G4int endOffset = (z > 0) ? 1000 : 0;
        fiberID = 10000 + endOffset + row * 100 + col;
        // Result: ZM: 10000-10799, ZP: 11000-11799

    } else if (volName.contains("SiPM_X")) {
        // X-SiPM: Use Y and Z position to determine row and layer
        G4double x = pos.x() / mm;
        G4double y = pos.y() / mm;
        G4double z = pos.z() / mm;

        // Construction: y = startY + iy * wrapperSize = -87.85 + iy * 25.1
        //             z = startZ + iz * wrapperSize = -50.2 + iz * 25.1
        // But X-SiPM has Y offset -3.0mm!

        G4int iy = static_cast<G4int>(std::round((y + 87.85 + 3.0) / 25.1));  // Account for -3mm offset
        G4int iz = static_cast<G4int>(std::round((z + 50.2) / 25.1));

        // Clamp to valid range
        iy = std::max(0, std::min(7, iy));
        iz = std::max(0, std::min(3, iz));

        // Phase 3.0: Add end-bit to distinguish XP (right) from XM (left)
        // Base ID: 20000 + iz*100 + iy
        // If x > 0 (XP, right end): add 1000
        // If x < 0 (XM, left end): no offset
        G4int endOffset = (x > 0) ? 1000 : 0;
        fiberID = 20000 + endOffset + iz * 100 + iy;
        // Result: XM: 20000-20399, XP: 21000-21399

    } else if (volName.contains("SiPM_Y")) {
        // Y-SiPM: Use X and Z position to determine col and layer
        G4double x = pos.x() / mm;
        G4double y = pos.y() / mm;
        G4double z = pos.z() / mm;

        // Construction: x = startX + ix * wrapperSize = -87.85 + ix * 25.1
        //             z = startZ + iz * wrapperSize = -50.2 + iz * 25.1
        // But Y-SiPM has X offset -3.0mm and Z offset +3.0mm!

        G4int ix = static_cast<G4int>(std::round((x + 87.85 + 3.0) / 25.1));  // Account for -3mm offset
        G4int iz = static_cast<G4int>(std::round((z - 3.0 + 50.2) / 25.1));  // Account for +3mm offset

        // Clamp to valid range
        ix = std::max(0, std::min(7, ix));
        iz = std::max(0, std::min(3, iz));

        // Phase 3.0: Add end-bit to distinguish YP (front) from YM (back)
        // Base ID: 30000 + iz*100 + ix
        // If y > 0 (YP, front end): add 1000
        // If y < 0 (YM, back end): no offset
        G4int endOffset = (y > 0) ? 1000 : 0;
        fiberID = 30000 + endOffset + iz * 100 + ix;
        // Result: YM: 30000-30399, YP: 31000-31399
    }

    // Calculate wavelength from energy (E = hc/λ, λ = 1240/E[eV])
    G4double wavelength = (1240.0 / (energy / eV));  // nm

    // Check if this is a WLS photon (around 490nm, green)
    // Or check creator process
    G4bool isWLSPhoton = false;
    const G4VProcess* creatorProcess = track->GetCreatorProcess();
    if (creatorProcess) {
        G4String processName = creatorProcess->GetProcessName();
        if (processName == "OpWLS") {
            isWLSPhoton = true;
            fTotalWLPHits++;
        }
    }

    // ================================================================
    // PHASE 3.0: IDEAL OPTICAL PHYSICS
    // ================================================================
    // All photons reaching the SiPM are recorded (100% detection).
    // Detector effects (PDE, dark counts, electronic jitter) will be
    // applied in a separate Python digitization layer.
    // ================================================================

    // Log the hit (useful for debugging)
    spdlog::debug("SiPM Hit: Vol={}, Pos=({:.2f}, {:.2f}, {:.2f}) mm, "
                  "Wavelength={:.1f} nm, FiberID={}, IsWLS={}",
                  volName, pos.x()/mm, pos.y()/mm, pos.z()/mm,
                  wavelength, fiberID, isWLSPhoton);

    // ============================================================
    // Phase 3.0: Save slim SiPM hit to ROOT file via OutputManager
    // ============================================================
    SiPMHit* sipmHits = OutputManager::Instance()->GetSiPMHits();

    // Add SLIM hit to ROOT output (ML-optimized)
    // Only Det_ID, Time, and Wavelength stored
    sipmHits->AddHit(
        fiberID,      // Detector ID (with end-bit encoding)
        hitTime,      // Hit time (ns)
        wavelength    // Wavelength (nm)
    );

    // Kill the optical photon after detection
    track->SetTrackStatus(fStopAndKill);

    return true;
}

void MuonCubeSiPMSensitiveDetector::EndOfEvent(G4HCofThisEvent*)
{
    if (fTotalOpticalHits > 0) {
        spdlog::info("MuonCube SiPM: Total optical hits = {}, WLS hits = {}",
                     fTotalOpticalHits, fTotalWLPHits);
    }
}

G4int MuonCubeSiPMSensitiveDetector::MapPositionToFiberID(
    const G4String& planeName, G4double x, G4double y, G4double z)
{
    // Array parameters (must match MuonCubeConstruction)
    constexpr G4double wrapperSize = 25.1;  // mm
    constexpr G4int nX = 8;  // Number of fibers in X direction
    constexpr G4int nY = 8;  // Number of fibers in Y direction
    constexpr G4int nZ = 4;  // Number of fibers in Z direction

    // Calculate array extents
    G4double halfSizeX = nX * wrapperSize / 2.0;
    G4double halfSizeY = nY * wrapperSize / 2.0;
    G4double halfSizeZ = nZ * wrapperSize / 2.0;

    G4int fiberID = -1;

    // Map position based on which plane was hit
    if (planeName.contains("Z+") || planeName.contains("Z-")) {
        // Z-plane: fibers are arranged in X-Y grid
        // Map x, y to grid indices
        G4double gridX = (x + halfSizeX) / wrapperSize;
        G4double gridY = (y + halfSizeY) / wrapperSize;

        G4int ix = static_cast<G4int>(gridX);
        G4int iy = static_cast<G4int>(gridY);

        // Encode as Z-fiber ID: layer (which is not applicable for planes) + row + col
        // For Z-fibers: use 10000 + iy*100 + ix (high range to distinguish from X/Y)
        if (ix >= 0 && ix < nX && iy >= 0 && iy < nY) {
            fiberID = 10000 + iy * 100 + ix;
        }

    } else if (planeName.contains("X+") || planeName.contains("X-")) {
        // X-plane: fibers are arranged in Y-Z grid
        G4double gridY = (y + halfSizeY) / wrapperSize;
        G4double gridZ = (z + halfSizeZ) / wrapperSize;

        G4int iy = static_cast<G4int>(gridY);
        G4int iz = static_cast<G4int>(gridZ);

        // Encode as X-fiber ID: 20000 + iz*100 + iy
        if (iy >= 0 && iy < nY && iz >= 0 && iz < nZ) {
            fiberID = 20000 + iz * 100 + iy;
        }

    } else if (planeName.contains("Y+") || planeName.contains("Y-")) {
        // Y-plane: fibers are arranged in X-Z grid
        G4double gridX = (x + halfSizeX) / wrapperSize;
        G4double gridZ = (z + halfSizeZ) / wrapperSize;

        G4int ix = static_cast<G4int>(gridX);
        G4int iz = static_cast<G4int>(gridZ);

        // Encode as Y-fiber ID: 30000 + iz*100 + ix
        if (ix >= 0 && ix < nX && iz >= 0 && iz < nZ) {
            fiberID = 30000 + iz * 100 + ix;
        }
    }

    return fiberID;
}

G4int MuonCubeSiPMSensitiveDetector::MapCopyNumberToFiberID(G4int copyNo)
{
    // Copy number scheme (must match MuonCubeConstruction):
    // - Z-SiPMs: 0-127 (8x8 grid at Z+ and Z-)
    //   - 0-63:   Z+ face (positive Z)
    //   - 64-127: Z- face (negative Z)
    // - X-SiPMs: 128-191 (8x4 grid at X+ and X-)
    //   - 128-159: X+ face (positive X)
    //   - 160-191: X- face (negative X)
    // - Y-SiPMs: 192-255 (8x4 grid at Y+ and Y-)
    //   - 192-223: Y+ face (positive Y)
    //   - 224-255: Y- face (negative Y)

    if (copyNo < 0 || copyNo > 255) {
        // Invalid copy number
        return -1;
    }

    G4int fiberID = -1;

    if (copyNo < 128) {
        // Z-SiPMs (0-127)
        G4int localIdx = copyNo % 64;  // 0-63 within one face
        G4int row = localIdx / 8;       // 0-7 (Y direction)
        G4int col = localIdx % 8;       // 0-7 (X direction)

        // Z-fiber ID encoding: 10000 + row*100 + col
        fiberID = 10000 + row * 100 + col;

    } else if (copyNo < 192) {
        // X-SiPMs (128-191)
        // Copy number assignment: Outer Y-loop (0-7), Inner Z-loop (0-3)
        // X+ face: copy 128-159, X- face: copy 160-191
        G4int localIdx = (copyNo - 128) % 32;  // 0-31 within one face
        G4int iy = localIdx / 4;               // 0-7 (Y direction, from outer loop)
        G4int iz = localIdx % 4;               // 0-3 (Z direction, from inner loop)

        // X-fiber ID encoding: 20000 + iz*100 + iy
        // Encodes layer (Z) and row (Y) positions
        fiberID = 20000 + iz * 100 + iy;

    } else {
        // Y-SiPMs (192-255)
        // Copy number assignment: Outer X-loop (0-7), Inner Z-loop (0-3)
        // Y+ face: copy 192-223, Y- face: copy 224-255
        G4int localIdx = (copyNo - 192) % 32;  // 0-31 within one face (same for Y+ and Y-)
        G4int ix = localIdx / 4;               // 0-7 (X direction, from outer loop)
        G4int iz = localIdx % 4;               // 0-3 (Z direction, from inner loop)

        // Y-fiber ID encoding: 30000 + iz*100 + ix
        // Encodes layer (Z) and column (X) positions
        fiberID = 30000 + iz * 100 + ix;
    }

    return fiberID;
}
