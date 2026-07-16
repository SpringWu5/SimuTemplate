/*
 * PhysicsList.hh
 * 
 * Created on: 2024.09.28
 * Author: Cen Mo
 */

#ifndef PHYSICSLIST_HH
#define PHYSICSLIST_HH

#include <CLHEP/Units/SystemOfUnits.h>
#include <boost/property_tree/ptree.hpp>

#include "globals.hh"
#include "G4VModularPhysicsList.hh"


class PhysicsList: public G4VModularPhysicsList{
public:
    PhysicsList(G4int verbose = 0);
    virtual ~PhysicsList();

    // SetCuts()
    virtual void SetCuts();
};
#endif