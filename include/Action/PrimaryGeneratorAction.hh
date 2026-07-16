/*
 * PrimaryGeneratorAction.hh
 *
 * Created on: 2024.09.28
 * Author: Cen Mo
 */

#ifndef PRIMARYGENERATORACTION_HH
#define PRIMARYGENERATORACTION_HH

#include "G4VUserPrimaryGeneratorAction.hh"
#include "G4ParticleGun.hh"
#include "G4GeneralParticleSource.hh"
#include "G4Event.hh"
#include "Record/McEvent.hh"
#include "nlohmann/json.hpp"
using json = nlohmann::json;

class PrimaryGeneratorAction : public G4VUserPrimaryGeneratorAction
{
public:
    PrimaryGeneratorAction(json particle_list);
    virtual ~PrimaryGeneratorAction();

    virtual void GeneratePrimaries(G4Event *);

    // Static counter to keep track of which muon to use next
    static G4int fNextMuonIndex;

private:
    G4ParticleGun*          fParticleGun;
    json                    fParticleList;
};

#endif
