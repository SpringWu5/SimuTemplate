
#ifndef EVENTACTION_HH
#define EVENTACTION_HH

#include "G4UserEventAction.hh"
#include "globals.hh"

#include "Record/OutputManager.hh"

class EventAction : public G4UserEventAction
{
public:
    EventAction();
    ~EventAction();
    virtual void BeginOfEventAction(const G4Event *);
    virtual void EndOfEventAction([[maybe_unused]] const G4Event *);

private:
    G4int fEventID;
};


#endif
