/*
 * SipmBuilder.hh
 * 
 * Created on: 2024.09.28
 * Author: Weilun Huang
 */

#ifndef SIPMBUILDER_HH
#define SIPMBUILDER_HH

#include "G4LogicalVolume.hh"

class G4Box;

class SipmBuilder
{
public:
    SipmBuilder();
    void Build();
    void BuildSolid();
    void BuildSurface();
    void BuildSD();
    G4LogicalVolume *GetLogicVolume() { return fLogicSipm; };

private:
    G4Box *fSolidSipm;
    G4LogicalVolume *fLogicSipm;

};

#endif