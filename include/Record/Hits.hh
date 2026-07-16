/*
 * Hits.hh
 * 
 * Created on: 2024.10.04
 * Author: Cen Mo
*/

#ifndef HITS_HH
#define HITS_HH

#include "TTree.h"
#include "vector"
#include "TString.h"

using std::vector;

enum HitType {
    OpticalPhoton = 0,
    Muon,
    Others
};

class Hits
{
public:
    Hits() {};
    ~Hits() {};

    void BookBranches(TTree* tree, TString prefix="") {
        tree->Branch(prefix + "Hit_type", &fHitType);
        tree->Branch(prefix + "Hit_Particle_ID", &fParticleID);
        tree->Branch(prefix + "Hit_Det_ID", &fHitDetID);
        tree->Branch(prefix + "Hit_energy", &fEnergy);
        tree->Branch(prefix + "Hit_px", &fHitPX);
        tree->Branch(prefix + "Hit_py", &fHitPY);
        tree->Branch(prefix + "Hit_pz", &fHitPZ);
        tree->Branch(prefix + "Hit_pos_x", &fHitPosX);
        tree->Branch(prefix + "Hit_pos_y", &fHitPosY);
        tree->Branch(prefix + "Hit_pos_z", &fHitPosZ);
        tree->Branch(prefix + "Hit_time", &fHitTime);
        tree->Branch(prefix + "Hit_stepLen", &fHitStepLen);
        // Phase 2.4: Optical photon wavelength (for SiPM readout)
        tree->Branch(prefix + "Hit_wavelength", &fHitWavelength);
    }

    void Reset() {
        fHitType.clear();
        fParticleID.clear();
        fHitDetID.clear();
        fEnergy.clear();
        fHitPX.clear();
        fHitPY.clear();
        fHitPZ.clear();
        fHitPosX.clear();
        fHitPosY.clear();
        fHitPosZ.clear();
        fHitTime.clear();
        fHitStepLen.clear();
        fHitWavelength.clear();
    }
    
    void AddHit(
            HitType type, int particleID, int detID,
            Float_t energy, Float_t px, Float_t py, Float_t pz,
            Float_t posX, Float_t posY, Float_t posZ, Float_t time,
            Float_t stepLen, Float_t wavelength = 0.0
        ) {
        fHitType.push_back(static_cast<unsigned int>(type));
        fParticleID.push_back(particleID);
        fHitDetID.push_back(detID);
        fEnergy.push_back(energy);
        fHitPX.push_back(px);
        fHitPY.push_back(py);
        fHitPZ.push_back(pz);
        fHitPosX.push_back(posX);
        fHitPosY.push_back(posY);
        fHitPosZ.push_back(posZ);
        fHitTime.push_back(time);
        fHitStepLen.push_back(stepLen);
        fHitWavelength.push_back(wavelength);
    }

    // const Getters
    vector<unsigned int> GetHitType() const { return fHitType; }
    vector<int> GetParticleID() const { return fParticleID; }
    vector<int> GetHitDetID() const { return fHitDetID; }
    vector<Float_t> GetEnergy() const { return fEnergy; }
    vector<Float_t> GetHitPX() const { return fHitPX; }
    vector<Float_t> GetHitPY() const { return fHitPY; }
    vector<Float_t> GetHitPZ() const { return fHitPZ; }
    vector<Float_t> GetHitPosX() const { return fHitPosX; }
    vector<Float_t> GetHitPosY() const { return fHitPosY; }
    vector<Float_t> GetHitPosZ() const { return fHitPosZ; }
    vector<Float_t> GetHitTime() const { return fHitTime; }
    vector<Float_t> GetHitStepLen() const { return fHitStepLen; }
    vector<Float_t> GetHitWavelength() const { return fHitWavelength; }

private:
    vector<unsigned int> fHitType;
    vector<int> fParticleID;
    vector<int> fHitDetID;
    vector<Float_t> fEnergy;
    vector<Float_t> fHitPX;
    vector<Float_t> fHitPY;
    vector<Float_t> fHitPZ;
    vector<Float_t> fHitPosX;
    vector<Float_t> fHitPosY;
    vector<Float_t> fHitPosZ;
    vector<Float_t> fHitTime;
    vector<Float_t> fHitStepLen;
    vector<Float_t> fHitWavelength;  // Phase 2.4: Optical wavelength (nm)
};


#endif