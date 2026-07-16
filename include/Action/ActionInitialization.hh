/*
 * ActionInitialization.hh
 *
 * Created on: 2024.09.28
 * Author: Cen Mo
 */

#ifndef ACTIONINITIALIZATION_HH
#define ACTIONINITIALIZATION_HH

#include "G4VUserActionInitialization.hh"
#include "nlohmann/json.hpp"
using json = nlohmann::json;

class ActionInitialization : public G4VUserActionInitialization
{
public:
    ActionInitialization(json& particle_list);
    virtual void Build() const;
    void setPrimaryGeneratorAction(G4VUserPrimaryGeneratorAction *pga) { fPga = pga; }
    void setEventAction(G4UserEventAction *eventAction) { fEventAction = eventAction; }
    void setRunAction(G4UserRunAction *runAction) { fRunAction = runAction; }

private:
    bool freproduction_mode;
    bool fUsePointSource;
    json fParticleList;
    G4VUserPrimaryGeneratorAction *fPga;
    G4UserEventAction *fEventAction;
    G4UserRunAction *fRunAction;
};

#endif
