/*
 * VoxelTruthHit.hh
 *
 * ML-Optimized Voxel-Level Truth Collection (Phase 3.0)
 * Tracks primary particle behavior through each scintillator voxel
 *
 * Created on: 2025
 * Author: Claude Code
 */

#ifndef VOXELTRUTHHIT_HH
#define VOXELTRUTHHIT_HH

#include "TTree.h"
#include "vector"
#include "map"
#include "TString.h"

using std::vector;
using std::map;

/**
 * @brief Voxel-level truth data structure
 *
 * Stores entry/exit dynamics of the primary particle for each voxel:
 * - Voxel ID (CopyNumber)
 * - Total energy deposited
 * - Total track length
 * - Entry state (position, time, kinetic energy)
 * - Exit state (position, time, kinetic energy)
 */
class VoxelTruthHit
{
public:
    VoxelTruthHit() {};
    ~VoxelTruthHit() {};

    void BookBranches(TTree* tree, TString prefix="") {
        tree->Branch(prefix + "ID", &fVoxelID);
        tree->Branch(prefix + "Edep", &fEdep);
        tree->Branch(prefix + "TrackLen", &fTrackLen);

        // Entry state
        tree->Branch(prefix + "Entry_X", &fEntryX);
        tree->Branch(prefix + "Entry_Y", &fEntryY);
        tree->Branch(prefix + "Entry_Z", &fEntryZ);
        tree->Branch(prefix + "Entry_T", &fEntryT);
        tree->Branch(prefix + "Entry_E", &fEntryE);

        // Exit state
        tree->Branch(prefix + "Exit_X", &fExitX);
        tree->Branch(prefix + "Exit_Y", &fExitY);
        tree->Branch(prefix + "Exit_Z", &fExitZ);
        tree->Branch(prefix + "Exit_T", &fExitT);
        tree->Branch(prefix + "Exit_E", &fExitE);
    }

    void Reset() {
        fVoxelID.clear();
        fEdep.clear();
        fTrackLen.clear();

        fEntryX.clear(); fEntryY.clear(); fEntryZ.clear();
        fEntryT.clear(); fEntryE.clear();

        fExitX.clear(); fExitY.clear(); fExitZ.clear();
        fExitT.clear(); fExitE.clear();

        fVoxelMap.clear();
    }

    /**
     * @brief Initialize a new voxel hit with entry state
     *
     * Called on FIRST primary step entering a voxel.
     * Sets the entry position, time, and kinetic energy.
     *
     * Note: If voxel was created by secondaries (AddEnergy called first),
     * this will UPDATE the entry/exit state from placeholder zeros to actual values.
     */
    void InitializeVoxel(int voxelID, double x, double y, double z,
                        double t, double kineticEnergy) {
        // Check if voxel already exists
        auto it = fVoxelMap.find(voxelID);
        if (it != fVoxelMap.end()) {
            // Voxel exists - check if it has placeholder entry (created by secondaries)
            size_t idx = it->second;
            if (fEntryE[idx] == 0.0 && fEntryT[idx] == 0.0) {
                // Placeholder entry from AddEnergy - update it now
                fEntryX[idx] = x; fEntryY[idx] = y; fEntryZ[idx] = z;
                fEntryT[idx] = t;
                fEntryE[idx] = kineticEnergy;

                // Also update exit state to match entry (will be updated by subsequent steps)
                fExitX[idx] = x; fExitY[idx] = y; fExitZ[idx] = z;
                fExitT[idx] = t;
                fExitE[idx] = kineticEnergy;
            }
            return;  // Already initialized (either now or previously)
        }

        // Store index for quick lookup
        size_t idx = fVoxelID.size();
        fVoxelMap[voxelID] = idx;

        // Initialize with zeros
        fVoxelID.push_back(voxelID);
        fEdep.push_back(0.0);
        fTrackLen.push_back(0.0);

        // Entry state
        fEntryX.push_back(x);
        fEntryY.push_back(y);
        fEntryZ.push_back(z);
        fEntryT.push_back(t);
        fEntryE.push_back(kineticEnergy);

        // Exit state (initialize to entry values)
        fExitX.push_back(x);
        fExitY.push_back(y);
        fExitZ.push_back(z);
        fExitT.push_back(t);
        fExitE.push_back(kineticEnergy);
    }

    /**
     * @brief Add energy deposition (called for ALL particles including secondaries)
     *
     * This accumulates energy from delta-rays, Bremsstrahlung, etc.
     * Critical for calorimetry - captures TOTAL energy deposited.
     */
    void AddEnergy(int voxelID, double edep) {
        // Check if voxel exists
        auto it = fVoxelMap.find(voxelID);
        if (it == fVoxelMap.end()) {
            // Voxel not yet initialized - create it with placeholder entry/exit
            // This handles delta-only voxels (hit only by secondaries)
            size_t idx = fVoxelID.size();
            fVoxelMap[voxelID] = idx;

            fVoxelID.push_back(voxelID);
            fEdep.push_back(edep);
            fTrackLen.push_back(0.0);  // No primary track

            // Entry/exit states set to 0 (no primary passed through)
            fEntryX.push_back(0.0); fEntryY.push_back(0.0); fEntryZ.push_back(0.0);
            fEntryT.push_back(0.0); fEntryE.push_back(0.0);

            fExitX.push_back(0.0);  fExitY.push_back(0.0);  fExitZ.push_back(0.0);
            fExitT.push_back(0.0);  fExitE.push_back(0.0);
        } else {
            // Voxel exists - just add energy
            size_t idx = it->second;
            fEdep[idx] += edep;
        }
    }

    /**
     * @brief Check if voxel has entry state set (primary has entered)
     *
     * Returns true if the primary particle has entered this voxel
     * (Entry_T > 0 indicates primary has initialized entry state)
     */
    bool HasEntryState(int voxelID) const {
        auto it = fVoxelMap.find(voxelID);
        if (it == fVoxelMap.end()) {
            return false;
        }
        size_t idx = it->second;
        return fEntryT[idx] > 0.0;  // Entry time > 0 means initialized
    }

    /**
     * @brief Update voxel with primary particle kinematics
     *
     * Called on EVERY primary step to:
     * - Accumulate track length (for primary trajectory)
     * - Update exit state (last step will remain)
     *
     * Note: Energy deposition is handled separately via AddEnergy()
     */
    void UpdateVoxel(int voxelID, double stepLen,
                    double x, double y, double z,
                    double t, double kineticEnergy) {
        auto it = fVoxelMap.find(voxelID);
        if (it == fVoxelMap.end()) {
            // Voxel not initialized - should not happen if InitializeVoxel was called first
            return;
        }

        size_t idx = it->second;

        // Accumulate track length (primary trajectory only)
        fTrackLen[idx] += stepLen;

        // Update exit state (last step will remain)
        fExitX[idx] = x;
        fExitY[idx] = y;
        fExitZ[idx] = z;
        fExitT[idx] = t;
        fExitE[idx] = kineticEnergy;
    }

    // Getters
    size_t GetNumVoxels() const { return fVoxelID.size(); }

    /**
     * @brief Get current track length for a voxel
     * Returns 0.0 if voxel doesn't exist yet
     */
    double GetTrackLen(int voxelID) const {
        auto it = fVoxelMap.find(voxelID);
        if (it == fVoxelMap.end()) {
            return 0.0;  // Voxel doesn't exist
        }
        size_t idx = it->second;
        return fTrackLen[idx];
    }

private:
    // Voxel identification and totals
    vector<int> fVoxelID;      // CopyNumber of scintillator voxel
    vector<double> fEdep;      // Total energy deposited (MeV)
    vector<double> fTrackLen;  // Total track length (mm)

    // Entry state (at first step)
    vector<double> fEntryX, fEntryY, fEntryZ;  // Position (mm)
    vector<double> fEntryT;                    // Time (ns)
    vector<double> fEntryE;                    // Kinetic energy (MeV)

    // Exit state (at last step)
    vector<double> fExitX, fExitY, fExitZ;    // Position (mm)
    vector<double> fExitT;                    // Time (ns)
    vector<double> fExitE;                    // Kinetic energy (MeV)

    // Map for quick voxel lookup
    map<int, size_t> fVoxelMap;
};

#endif // VOXELTRUTHHIT_HH
