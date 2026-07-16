
#ifndef RUNACTION_HH
#define RUNACTION_HH

#include "globals.hh"
#include "G4UserRunAction.hh"

class G4Timer;
class G4VPhysicalVolume;

class RunAction : public G4UserRunAction
{
public:
    RunAction();
    virtual ~RunAction();

    virtual void BeginOfRunAction(const G4Run *);
    virtual void EndOfRunAction(const G4Run *);

    // Set world volume for geometry export (call before BeginOfRunAction)
    void SetWorldVolume(G4VPhysicalVolume* world) { fWorldVolume = world; }

private:
    G4Timer *fTimer;
    G4VPhysicalVolume* fWorldVolume;  // World volume for geometry export
};

#endif
