#include "G4ParticleDefinition.hh"
#include "G4ParticleGun.hh"
#include "G4ParticleTable.hh"
#include "G4SystemOfUnits.hh"
#include "Randomize.hh"
#include "spdlog/spdlog.h"
#include <cmath>

#include "Record/OutputManager.hh"
#include "Record/Muons.hh"
#include "Action/PrimaryGeneratorAction.hh"

// Initialize static counter
G4int PrimaryGeneratorAction::fNextMuonIndex = 0;

PrimaryGeneratorAction::PrimaryGeneratorAction(json particle_list)
    : G4VUserPrimaryGeneratorAction(),
    fParticleList(particle_list) {
    spdlog::info("PrimaryGeneratorAction: Initialize JSON mode");
    fParticleGun = new G4ParticleGun(1);
}

PrimaryGeneratorAction::~PrimaryGeneratorAction() {
    delete fParticleGun;
}

void PrimaryGeneratorAction::GeneratePrimaries(G4Event *event) {
    // Get the next muon index, taking into account looping
    int idx = fNextMuonIndex % fParticleList.size();
    fNextMuonIndex++; // Increment for next time
    
    // To record muon info
    Muons* muons = OutputManager::Instance()->GetMuons();

    auto particleTable = G4ParticleTable::GetParticleTable();

    auto mc_event = fParticleList[idx].get<McEvent>();

    // record event weight
    muons->SetWeightSpectrum(mc_event.weight_spectrum);

    int numParticles = mc_event.particles_at_detector.size();
    G4PrimaryVertex **vecPrimaryVertex = new G4PrimaryVertex *[numParticles];

    for (int i = 0; i < numParticles; i++) {
        vecPrimaryVertex[i] = new G4PrimaryVertex;
        const auto &mcParticle = mc_event.particles_at_detector[i];

        // Use actual particle position from JSON
        vecPrimaryVertex[i]->SetPosition(mcParticle.x * cm, mcParticle.y * cm,
                                        mcParticle.z * cm);
        vecPrimaryVertex[i]->SetT0(mcParticle.t * ns);
        
        auto particleDef = particleTable->FindParticle(mcParticle.pdgid);
        if (particleDef == nullptr) {
            spdlog::warn("Can not find particle with pdgid {:d}", mcParticle.pdgid);
        }
        // CRITICAL FIX: JSON momentum is in MeV, not GeV
        G4PrimaryParticle *particle =
            new G4PrimaryParticle(particleDef, mcParticle.px * MeV,
                                    mcParticle.py * MeV, mcParticle.pz * MeV);
        vecPrimaryVertex[i]->SetPrimary(particle);

        // Record muons (momentum in MeV from JSON)
        muons->AddMuon(mcParticle.px, mcParticle.py, mcParticle.pz);
        event->AddPrimaryVertex(vecPrimaryVertex[i]);

        // --- DEBUG MUON RECORDING START ---
        // Debug what's being stored in Muons object
        if (event->GetEventID() < 3 && i == 0) { // Only first particle of first 3 events
            G4cout << ">>> [MUON-DEBUG] Event " << event->GetEventID()
                   << " AFTER AddMuon:" << G4endl
                   << "    JSON Mom: (" << mcParticle.px << ", "
                   << mcParticle.py << ", " << mcParticle.pz << ")" << G4endl;
            // Note: We can't easily access the stored muon data here since it's in a private vector
            // But we can verify the input was correct from the debug above
        }
        // --- DEBUG MUON RECORDING END ---

        // --- DIAGNOSTIC PROBE START ---
        // Print first 5 events to verify particle generation
        if (event->GetEventID() < 5) {
            G4double p_total = std::sqrt(mcParticle.px*mcParticle.px +
                                        mcParticle.py*mcParticle.py +
                                        mcParticle.pz*mcParticle.pz);
            G4cout << ">>> [DEBUG] Event " << event->GetEventID()
                   << " Primary Particle #" << i << G4endl
                   << "    PDG: " << mcParticle.pdgid << G4endl
                   << "    Pos(cm): (" << mcParticle.x << ", " << mcParticle.y
                   << ", " << mcParticle.z << ")" << G4endl
                   << "    Pos(mm): (" << mcParticle.x*10 << ", " << mcParticle.y*10
                   << ", " << mcParticle.z*10 << ")" << G4endl
                   << "    Mom(MeV): (" << mcParticle.px << ", " << mcParticle.py
                   << ", " << mcParticle.pz << ")" << G4endl
                   << "    |p|: " << p_total << " MeV" << G4endl;
        }
        // --- DIAGNOSTIC PROBE END ---
    }
    delete[] vecPrimaryVertex;

    spdlog::info("Generated primary particles for event {}, using muon data index {}",
                event->GetEventID(), idx);
}
