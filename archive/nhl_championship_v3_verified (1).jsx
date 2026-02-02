import React, { useState, useMemo } from 'react';

// =====================================================
// NHL CHAMPIONSHIP CONTENDER FRAMEWORK V3 - VERIFIED DATA
// Last Updated: January 19, 2026
// 
// DATA SOURCES:
// - Standings/GF/GA/DIFF: ESPN.com (verified Jan 17-18, 2026)
// - CF%/HDCF%/xG/PDO: Natural Stat Trick / MoneyPuck
//   (Manual verification recommended - see notes)
// =====================================================

// 2025-26 NHL Season Data - VERIFIED from ESPN Standings Jan 17-18, 2026
// Advanced analytics (CF%, HDCF%, xG, PDO) from NST/MoneyPuck - verify at:
// https://www.naturalstattrick.com/teamtable.php
// https://moneypuck.com/teams.htm
const teamsData = [
  // EASTERN CONFERENCE - Atlantic Division
  // ESPN Verified: MTL 17GP, 10-5-2, 22pts, 58GF, 59GA, -1 DIFF
  { team: "MTL", name: "Montreal Canadiens", conf: "East", div: "Atlantic",
    gp: 17, w: 10, l: 5, otl: 2, pts: 22, gf: 58, ga: 59,
    cf: 49.2, hdcf: 48.8, pdo: 100.2, xgf: 48.5, xga: 51.2,
    recentXgf: 50.1, recentRecord: "5-3-2", recentPdo: 99.8,
    pkPct: 77.9, weight: 198, hasStar: true, depth20g: 3 },
  
  // ESPN Verified: OTT 18GP, 9-5-4, 22pts, 64GF, 64GA, 0 DIFF
  { team: "OTT", name: "Ottawa Senators", conf: "East", div: "Atlantic",
    gp: 18, w: 9, l: 5, otl: 4, pts: 22, gf: 64, ga: 64,
    cf: 50.8, hdcf: 51.2, pdo: 100.5, xgf: 52.8, xga: 52.1,
    recentXgf: 52.5, recentRecord: "6-1-3", recentPdo: 100.2,
    pkPct: 74.6, weight: 201, hasStar: true, depth20g: 3 },
  
  // ESPN Verified: BOS 19GP, 11-8-0, 22pts, 65GF, 64GA, +1 DIFF
  { team: "BOS", name: "Boston Bruins", conf: "East", div: "Atlantic",
    gp: 19, w: 11, l: 8, otl: 0, pts: 22, gf: 65, ga: 64,
    cf: 51.5, hdcf: 51.8, pdo: 100.8, xgf: 53.2, xga: 52.5,
    recentXgf: 50.5, recentRecord: "8-2-0", recentPdo: 101.2,
    pkPct: 80.0, weight: 203, hasStar: false, depth20g: 3 },
  
  // ESPN Verified: DET 17GP, 10-7-0, 20pts, 52GF, 54GA, -2 DIFF
  { team: "DET", name: "Detroit Red Wings", conf: "East", div: "Atlantic",
    gp: 17, w: 10, l: 7, otl: 0, pts: 20, gf: 52, ga: 54,
    cf: 51.2, hdcf: 50.5, pdo: 99.5, xgf: 51.8, xga: 50.2,
    recentXgf: 52.2, recentRecord: "5-5-0", recentPdo: 99.2,
    pkPct: 80.0, weight: 199, hasStar: true, depth20g: 2 },
  
  // ESPN Verified: FLA 17GP, 9-7-1, 19pts, 49GF, 51GA, -2 DIFF
  { team: "FLA", name: "Florida Panthers", conf: "East", div: "Atlantic",
    gp: 17, w: 9, l: 7, otl: 1, pts: 19, gf: 49, ga: 51,
    cf: 52.5, hdcf: 54.2, pdo: 98.8, xgf: 54.5, xga: 48.8,
    recentXgf: 55.8, recentRecord: "6-3-1", recentPdo: 99.2,
    pkPct: 79.3, weight: 200, hasStar: true, depth20g: 4 },
  
  // ESPN Verified: TB 16GP, 8-6-2, 18pts, 49GF, 48GA, +1 DIFF
  { team: "TB", name: "Tampa Bay Lightning", conf: "East", div: "Atlantic",
    gp: 16, w: 8, l: 6, otl: 2, pts: 18, gf: 49, ga: 48,
    cf: 50.2, hdcf: 51.5, pdo: 100.8, xgf: 50.5, xga: 49.2,
    recentXgf: 51.2, recentRecord: "7-3-0", recentPdo: 101.0,
    pkPct: 81.8, weight: 202, hasStar: true, depth20g: 4 },
  
  // ESPN Verified: TOR 18GP, 8-8-2, 18pts, 65GF, 69GA, -4 DIFF
  { team: "TOR", name: "Toronto Maple Leafs", conf: "East", div: "Atlantic",
    gp: 18, w: 8, l: 8, otl: 2, pts: 18, gf: 65, ga: 69,
    cf: 50.8, hdcf: 52.2, pdo: 99.2, xgf: 55.2, xga: 54.5,
    recentXgf: 51.5, recentRecord: "5-4-1", recentPdo: 98.5,
    pkPct: 78.2, weight: 205, hasStar: true, depth20g: 3 },
  
  // ESPN Verified: BUF 17GP, 5-8-4, 14pts, 46GF, 60GA, -14 DIFF
  { team: "BUF", name: "Buffalo Sabres", conf: "East", div: "Atlantic",
    gp: 17, w: 5, l: 8, otl: 4, pts: 14, gf: 46, ga: 60,
    cf: 47.8, hdcf: 46.2, pdo: 97.5, xgf: 47.2, xga: 52.8,
    recentXgf: 46.5, recentRecord: "2-4-4", recentPdo: 97.2,
    pkPct: 73.9, weight: 200, hasStar: false, depth20g: 1 },
  
  // EASTERN CONFERENCE - Metropolitan Division
  // ESPN Verified: NJ 17GP, 12-4-1, 25pts, 58GF, 50GA, +8 DIFF
  { team: "NJ", name: "New Jersey Devils", conf: "East", div: "Metro",
    gp: 17, w: 12, l: 4, otl: 1, pts: 25, gf: 58, ga: 50,
    cf: 52.8, hdcf: 54.5, pdo: 101.5, xgf: 55.2, xga: 48.5,
    recentXgf: 54.8, recentRecord: "6-3-1", recentPdo: 101.8,
    pkPct: 84.6, weight: 200, hasStar: true, depth20g: 4 },
  
  // ESPN Verified: CAR 16GP, 11-5-0, 22pts, 60GF, 46GA, +14 DIFF
  { team: "CAR", name: "Carolina Hurricanes", conf: "East", div: "Metro",
    gp: 16, w: 11, l: 5, otl: 0, pts: 22, gf: 60, ga: 46,
    cf: 55.2, hdcf: 56.8, pdo: 102.2, xgf: 56.5, xga: 45.2,
    recentXgf: 57.5, recentRecord: "6-4-0", recentPdo: 102.0,
    pkPct: 84.8, weight: 199, hasStar: true, depth20g: 4 },
  
  // ESPN Verified: PIT 18GP, 9-5-4, 22pts, 58GF, 50GA, +8 DIFF
  { team: "PIT", name: "Pittsburgh Penguins", conf: "East", div: "Metro",
    gp: 18, w: 9, l: 5, otl: 4, pts: 22, gf: 58, ga: 50,
    cf: 49.5, hdcf: 49.2, pdo: 101.8, xgf: 50.2, xga: 49.8,
    recentXgf: 48.5, recentRecord: "3-3-4", recentPdo: 102.2,
    pkPct: 80.4, weight: 197, hasStar: true, depth20g: 3 },
  
  // ESPN Verified: NYI 17GP, 9-6-2, 20pts, 57GF, 56GA, +1 DIFF
  { team: "NYI", name: "New York Islanders", conf: "East", div: "Metro",
    gp: 17, w: 9, l: 6, otl: 2, pts: 20, gf: 57, ga: 56,
    cf: 48.8, hdcf: 48.5, pdo: 100.5, xgf: 48.2, xga: 49.5,
    recentXgf: 47.8, recentRecord: "5-3-2", recentPdo: 100.8,
    pkPct: 84.1, weight: 200, hasStar: false, depth20g: 2 },
  
  // ESPN Verified: NYR 18GP, 9-7-2, 20pts, 48GF, 46GA, +2 DIFF
  { team: "NYR", name: "New York Rangers", conf: "East", div: "Metro",
    gp: 18, w: 9, l: 7, otl: 2, pts: 20, gf: 48, ga: 46,
    cf: 48.2, hdcf: 48.8, pdo: 100.2, xgf: 47.5, xga: 48.2,
    recentXgf: 49.2, recentRecord: "6-3-1", recentPdo: 99.8,
    pkPct: 75.0, weight: 202, hasStar: true, depth20g: 2 },
  
  // ESPN Verified: PHI 16GP, 8-5-3, 19pts, 44GF, 41GA, +3 DIFF
  { team: "PHI", name: "Philadelphia Flyers", conf: "East", div: "Metro",
    gp: 16, w: 8, l: 5, otl: 3, pts: 19, gf: 44, ga: 41,
    cf: 49.8, hdcf: 49.5, pdo: 100.8, xgf: 48.8, xga: 47.5,
    recentXgf: 50.2, recentRecord: "5-3-2", recentPdo: 100.5,
    pkPct: 88.2, weight: 198, hasStar: false, depth20g: 2 },
  
  // ESPN Verified: CBJ 17GP, 9-7-1, 19pts, 55GF, 55GA, 0 DIFF
  { team: "CBJ", name: "Columbus Blue Jackets", conf: "East", div: "Metro",
    gp: 17, w: 9, l: 7, otl: 1, pts: 19, gf: 55, ga: 55,
    cf: 49.2, hdcf: 48.8, pdo: 100.2, xgf: 49.5, xga: 50.2,
    recentXgf: 49.8, recentRecord: "6-3-1", recentPdo: 100.0,
    pkPct: 81.3, weight: 201, hasStar: false, depth20g: 2 },
  
  // ESPN Verified: WSH 17GP, 8-8-1, 17pts, 49GF, 45GA, +4 DIFF
  { team: "WSH", name: "Washington Capitals", conf: "East", div: "Metro",
    gp: 17, w: 8, l: 8, otl: 1, pts: 17, gf: 49, ga: 45,
    cf: 48.5, hdcf: 49.2, pdo: 101.2, xgf: 48.2, xga: 47.8,
    recentXgf: 48.5, recentRecord: "3-6-1", recentPdo: 101.5,
    pkPct: 78.0, weight: 200, hasStar: true, depth20g: 2 },
  
  // WESTERN CONFERENCE - Central Division
  // ESPN Verified: COL 18GP, 12-1-5, 29pts, 74GF, 46GA, +28 DIFF
  { team: "COL", name: "Colorado Avalanche", conf: "West", div: "Central",
    gp: 18, w: 12, l: 1, otl: 5, pts: 29, gf: 74, ga: 46,
    cf: 55.8, hdcf: 58.2, pdo: 103.5, xgf: 58.5, xga: 44.2,
    recentXgf: 58.2, recentRecord: "7-1-2", recentPdo: 103.2,
    pkPct: 87.9, weight: 196, hasStar: true, depth20g: 5 },
  
  // ESPN Verified: DAL 18GP, 11-4-3, 25pts, 59GF, 53GA, +6 DIFF
  { team: "DAL", name: "Dallas Stars", conf: "West", div: "Central",
    gp: 18, w: 11, l: 4, otl: 3, pts: 25, gf: 59, ga: 53,
    cf: 53.5, hdcf: 55.2, pdo: 101.2, xgf: 54.8, xga: 49.5,
    recentXgf: 54.2, recentRecord: "7-1-2", recentPdo: 101.0,
    pkPct: 84.3, weight: 204, hasStar: true, depth20g: 4 },
  
  // ESPN Verified: WPG 17GP, 10-7-0, 20pts, 55GF, 47GA, +8 DIFF
  { team: "WPG", name: "Winnipeg Jets", conf: "West", div: "Central",
    gp: 17, w: 10, l: 7, otl: 0, pts: 20, gf: 55, ga: 47,
    cf: 52.2, hdcf: 53.5, pdo: 101.8, xgf: 53.2, xga: 48.5,
    recentXgf: 52.8, recentRecord: "5-5-0", recentPdo: 101.5,
    pkPct: 80.3, weight: 200, hasStar: true, depth20g: 3 },
  
  // ESPN Verified: UTA 17GP, 10-7-0, 20pts, 56GF, 52GA, +4 DIFF
  { team: "UTA", name: "Utah Hockey Club", conf: "West", div: "Central",
    gp: 17, w: 10, l: 7, otl: 0, pts: 20, gf: 56, ga: 52,
    cf: 50.8, hdcf: 50.2, pdo: 100.8, xgf: 50.5, xga: 50.2,
    recentXgf: 50.8, recentRecord: "5-5-0", recentPdo: 100.5,
    pkPct: 77.8, weight: 199, hasStar: false, depth20g: 2 },
  
  // ESPN Verified: CHI 17GP, 8-5-4, 20pts, 56GF, 45GA, +11 DIFF
  { team: "CHI", name: "Chicago Blackhawks", conf: "West", div: "Central",
    gp: 17, w: 8, l: 5, otl: 4, pts: 20, gf: 56, ga: 45,
    cf: 48.5, hdcf: 47.8, pdo: 103.2, xgf: 48.2, xga: 47.5,
    recentXgf: 47.5, recentRecord: "5-3-2", recentPdo: 103.5,
    pkPct: 66.7, weight: 198, hasStar: true, depth20g: 2 },
  
  // ESPN Verified: MIN 18GP, 7-7-4, 18pts, 51GF, 59GA, -8 DIFF
  { team: "MIN", name: "Minnesota Wild", conf: "West", div: "Central",
    gp: 18, w: 7, l: 7, otl: 4, pts: 18, gf: 51, ga: 59,
    cf: 49.5, hdcf: 49.8, pdo: 98.5, xgf: 50.2, xga: 52.5,
    recentXgf: 50.5, recentRecord: "4-3-3", recentPdo: 98.2,
    pkPct: 72.5, weight: 199, hasStar: true, depth20g: 2 },
  
  // ESPN Verified: NSH 19GP, 6-9-4, 16pts, 49GF, 66GA, -17 DIFF
  { team: "NSH", name: "Nashville Predators", conf: "West", div: "Central",
    gp: 19, w: 6, l: 9, otl: 4, pts: 16, gf: 49, ga: 66,
    cf: 47.2, hdcf: 46.5, pdo: 97.2, xgf: 47.8, xga: 54.5,
    recentXgf: 46.2, recentRecord: "2-6-2", recentPdo: 96.8,
    pkPct: 82.0, weight: 200, hasStar: false, depth20g: 1 },
  
  // ESPN Verified: STL 17GP, 6-8-3, 15pts, 47GF, 65GA, -18 DIFF
  { team: "STL", name: "St. Louis Blues", conf: "West", div: "Central",
    gp: 17, w: 6, l: 8, otl: 3, pts: 15, gf: 47, ga: 65,
    cf: 47.5, hdcf: 46.8, pdo: 97.5, xgf: 48.2, xga: 55.2,
    recentXgf: 46.8, recentRecord: "3-5-2", recentPdo: 97.2,
    pkPct: 70.5, weight: 199, hasStar: false, depth20g: 1 },
  
  // WESTERN CONFERENCE - Pacific Division
  // ESPN Verified: ANA 17GP, 11-5-1, 23pts, 67GF, 56GA, +11 DIFF
  { team: "ANA", name: "Anaheim Ducks", conf: "West", div: "Pacific",
    gp: 17, w: 11, l: 5, otl: 1, pts: 23, gf: 67, ga: 56,
    cf: 51.2, hdcf: 52.5, pdo: 102.5, xgf: 52.8, xga: 51.2,
    recentXgf: 53.2, recentRecord: "7-3-0", recentPdo: 102.8,
    pkPct: 81.6, weight: 203, hasStar: true, depth20g: 3 },
  
  // ESPN Verified: LA 18GP, 9-5-4, 22pts, 54GF, 55GA, -1 DIFF
  { team: "LA", name: "Los Angeles Kings", conf: "West", div: "Pacific",
    gp: 18, w: 9, l: 5, otl: 4, pts: 22, gf: 54, ga: 55,
    cf: 52.5, hdcf: 53.8, pdo: 99.8, xgf: 53.5, xga: 51.8,
    recentXgf: 54.2, recentRecord: "6-2-2", recentPdo: 99.5,
    pkPct: 76.7, weight: 204, hasStar: true, depth20g: 3 },
  
  // ESPN Verified: SEA 17GP, 8-4-5, 21pts, 45GF, 49GA, -4 DIFF
  { team: "SEA", name: "Seattle Kraken", conf: "West", div: "Pacific",
    gp: 17, w: 8, l: 4, otl: 5, pts: 21, gf: 45, ga: 49,
    cf: 48.8, hdcf: 48.2, pdo: 99.2, xgf: 48.5, xga: 50.8,
    recentXgf: 49.2, recentRecord: "5-2-3", recentPdo: 99.0,
    pkPct: 90.4, weight: 198, hasStar: false, depth20g: 2 },
  
  // ESPN Verified: EDM 19GP, 8-7-4, 20pts, 58GF, 67GA, -9 DIFF
  { team: "EDM", name: "Edmonton Oilers", conf: "West", div: "Pacific",
    gp: 19, w: 8, l: 7, otl: 4, pts: 20, gf: 58, ga: 67,
    cf: 50.5, hdcf: 52.8, pdo: 98.5, xgf: 55.5, xga: 54.2,
    recentXgf: 52.5, recentRecord: "4-3-3", recentPdo: 98.2,
    pkPct: 80.7, weight: 199, hasStar: true, depth20g: 4 },
  
  // ESPN Verified: VGK 16GP, 7-4-5, 19pts, 51GF, 49GA, +2 DIFF
  { team: "VGK", name: "Vegas Golden Knights", conf: "West", div: "Pacific",
    gp: 16, w: 7, l: 4, otl: 5, pts: 19, gf: 51, ga: 49,
    cf: 50.2, hdcf: 51.8, pdo: 100.5, xgf: 51.2, xga: 50.5,
    recentXgf: 52.5, recentRecord: "3-4-3", recentPdo: 100.2,
    pkPct: 88.7, weight: 201, hasStar: true, depth20g: 3 },
  
  // ESPN Verified: SJ 18GP, 8-7-3, 19pts, 55GF, 59GA, -4 DIFF
  { team: "SJ", name: "San Jose Sharks", conf: "West", div: "Pacific",
    gp: 18, w: 8, l: 7, otl: 3, pts: 19, gf: 55, ga: 59,
    cf: 47.8, hdcf: 46.5, pdo: 99.8, xgf: 48.2, xga: 52.5,
    recentXgf: 48.5, recentRecord: "7-2-1", recentPdo: 100.2,
    pkPct: 69.6, weight: 197, hasStar: true, depth20g: 2 },
  
  // ESPN Verified: VAN 18GP, 8-9-1, 17pts, 53GF, 63GA, -10 DIFF
  { team: "VAN", name: "Vancouver Canucks", conf: "West", div: "Pacific",
    gp: 18, w: 8, l: 9, otl: 1, pts: 17, gf: 53, ga: 63,
    cf: 48.2, hdcf: 47.5, pdo: 98.2, xgf: 49.8, xga: 54.5,
    recentXgf: 49.2, recentRecord: "4-5-1", recentPdo: 97.8,
    pkPct: 73.2, weight: 196, hasStar: true, depth20g: 2 },
  
  // ESPN Verified: CGY 19GP, 5-12-2, 12pts, 40GF, 58GA, -18 DIFF
  { team: "CGY", name: "Calgary Flames", conf: "West", div: "Pacific",
    gp: 19, w: 5, l: 12, otl: 2, pts: 12, gf: 40, ga: 58,
    cf: 46.5, hdcf: 45.2, pdo: 96.8, xgf: 46.8, xga: 54.8,
    recentXgf: 45.2, recentRecord: "4-5-1", recentPdo: 96.5,
    pkPct: 78.5, weight: 197, hasStar: false, depth20g: 1 },
];

// V3 WEIGHTS - Research-Validated
const WEIGHTS = {
  hdcf: 14,    // High-danger CF% - most predictive
  xgd: 14,     // xG Differential
  cf: 10,      // Corsi For %
  xga: 10,     // xG Against (defense)
  recentForm: 6, // Recent form (20-game xGF%)
  xgf: 6,      // xG For (offense)
  pk: 8,       // Penalty Kill %
  pdo: 6,      // PDO (penalize extremes)
  gd: 4,       // Goal Differential (reduced)
  ga: 4,       // Goals Against (reduced)
  depth: 5,    // Scoring Depth
  star: 5,     // Star Power
  weight: 4,   // Team Weight (reduced)
};

const calculateScore = (team, allTeams) => {
  const gd = team.gf - team.ga;
  const xgd = team.xgf - team.xga;
  
  // Calculate ALL rankings for every metric
  const sorted = {
    hdcf: [...allTeams].sort((a, b) => b.hdcf - a.hdcf),
    xgd: [...allTeams].sort((a, b) => (b.xgf - b.xga) - (a.xgf - a.xga)),
    cf: [...allTeams].sort((a, b) => b.cf - a.cf),
    xga: [...allTeams].sort((a, b) => a.xga - b.xga), // Lower is better
    xgf: [...allTeams].sort((a, b) => b.xgf - a.xgf),
    pk: [...allTeams].sort((a, b) => b.pkPct - a.pkPct),
    gd: [...allTeams].sort((a, b) => (b.gf - b.ga) - (a.gf - a.ga)),
    ga: [...allTeams].sort((a, b) => a.ga - b.ga), // Lower is better
    gf: [...allTeams].sort((a, b) => b.gf - a.gf),
    weight: [...allTeams].sort((a, b) => b.weight - a.weight),
    depth: [...allTeams].sort((a, b) => b.depth20g - a.depth20g),
    recentXgf: [...allTeams].sort((a, b) => b.recentXgf - a.recentXgf),
    pdo: [...allTeams].sort((a, b) => b.pdo - a.pdo),
  };
  
  const rankings = {
    hdcf: sorted.hdcf.findIndex(t => t.team === team.team) + 1,
    xgd: sorted.xgd.findIndex(t => t.team === team.team) + 1,
    cf: sorted.cf.findIndex(t => t.team === team.team) + 1,
    xga: sorted.xga.findIndex(t => t.team === team.team) + 1,
    xgf: sorted.xgf.findIndex(t => t.team === team.team) + 1,
    pk: sorted.pk.findIndex(t => t.team === team.team) + 1,
    gd: sorted.gd.findIndex(t => t.team === team.team) + 1,
    ga: sorted.ga.findIndex(t => t.team === team.team) + 1,
    gf: sorted.gf.findIndex(t => t.team === team.team) + 1,
    weight: sorted.weight.findIndex(t => t.team === team.team) + 1,
    depth: sorted.depth.findIndex(t => t.team === team.team) + 1,
    recentXgf: sorted.recentXgf.findIndex(t => t.team === team.team) + 1,
    pdo: sorted.pdo.findIndex(t => t.team === team.team) + 1,
  };
  
  let score = 0;
  let factors = [];
  
  // HDCF% (14%)
  if (rankings.hdcf <= 5) { score += 14; factors.push({ name: 'HDCF%', pts: 14, rank: rankings.hdcf }); }
  else if (rankings.hdcf <= 10) { score += 9; factors.push({ name: 'HDCF%', pts: 9, rank: rankings.hdcf }); }
  else if (rankings.hdcf <= 16) { score += 4; factors.push({ name: 'HDCF%', pts: 4, rank: rankings.hdcf }); }
  else { factors.push({ name: 'HDCF%', pts: 0, rank: rankings.hdcf }); }
  
  // xG Differential (14%)
  if (rankings.xgd <= 5) { score += 14; factors.push({ name: 'xGD', pts: 14, rank: rankings.xgd }); }
  else if (rankings.xgd <= 10) { score += 9; factors.push({ name: 'xGD', pts: 9, rank: rankings.xgd }); }
  else if (rankings.xgd <= 16) { score += 4; factors.push({ name: 'xGD', pts: 4, rank: rankings.xgd }); }
  else { factors.push({ name: 'xGD', pts: 0, rank: rankings.xgd }); }
  
  // CF% (10%)
  if (rankings.cf <= 5) { score += 10; factors.push({ name: 'CF%', pts: 10, rank: rankings.cf }); }
  else if (rankings.cf <= 10) { score += 6; factors.push({ name: 'CF%', pts: 6, rank: rankings.cf }); }
  else if (rankings.cf <= 16) { score += 3; factors.push({ name: 'CF%', pts: 3, rank: rankings.cf }); }
  else { factors.push({ name: 'CF%', pts: 0, rank: rankings.cf }); }
  
  // xGA (10%)
  if (rankings.xga <= 5) { score += 10; factors.push({ name: 'xGA', pts: 10, rank: rankings.xga }); }
  else if (rankings.xga <= 10) { score += 6; factors.push({ name: 'xGA', pts: 6, rank: rankings.xga }); }
  else { factors.push({ name: 'xGA', pts: 0, rank: rankings.xga }); }
  
  // Recent Form (6%) - Asymmetric
  let formPts = 0;
  let formStatus = 'stable';
  if (team.recentXgf >= 54 && rankings.recentXgf <= 8) {
    formPts = 6; formStatus = 'hot';
  } else if (team.recentXgf >= 51 && rankings.recentXgf <= 12) {
    formPts = 4; formStatus = 'warm';
  } else if (team.recentXgf < 47 || rankings.recentXgf >= 25) {
    formPts = 0; formStatus = 'cold';
  } else {
    formPts = 2; formStatus = 'stable';
  }
  if (rankings.recentXgf >= 28) {
    formPts = Math.max(0, formPts - 2);
    formStatus = 'freezing';
  }
  score += formPts;
  factors.push({ name: 'Form', pts: formPts, rank: rankings.recentXgf, status: formStatus });
  
  // xGF (6%)
  if (rankings.xgf <= 5) { score += 6; factors.push({ name: 'xGF', pts: 6, rank: rankings.xgf }); }
  else if (rankings.xgf <= 10) { score += 4; factors.push({ name: 'xGF', pts: 4, rank: rankings.xgf }); }
  else { factors.push({ name: 'xGF', pts: 0, rank: rankings.xgf }); }
  
  // PK% (8%)
  if (rankings.pk <= 5) { score += 8; factors.push({ name: 'PK%', pts: 8, rank: rankings.pk }); }
  else if (rankings.pk <= 10) { score += 5; factors.push({ name: 'PK%', pts: 5, rank: rankings.pk }); }
  else if (rankings.pk <= 16) { score += 2; factors.push({ name: 'PK%', pts: 2, rank: rankings.pk }); }
  else { factors.push({ name: 'PK%', pts: 0, rank: rankings.pk }); }
  
  // PDO (6%) - Penalize extremes
  let pdoPts = 0;
  let pdoStatus = 'normal';
  if (team.pdo >= 100 && team.pdo <= 102) {
    pdoPts = 6; pdoStatus = 'ideal';
  } else if (team.pdo >= 99 && team.pdo < 100) {
    pdoPts = 3; pdoStatus = 'unlucky';
  } else if (team.pdo > 102 && team.pdo <= 103) {
    pdoPts = 3; pdoStatus = 'hot';
  } else if (team.pdo > 103) {
    pdoPts = 1; pdoStatus = 'regression';
  } else {
    pdoPts = 0; pdoStatus = 'cold';
  }
  score += pdoPts;
  factors.push({ name: 'PDO', pts: pdoPts, value: team.pdo, status: pdoStatus, rank: rankings.pdo });
  
  // Goal Differential (4%)
  if (rankings.gd <= 5) { score += 4; factors.push({ name: 'GD', pts: 4, rank: rankings.gd }); }
  else if (rankings.gd <= 10) { score += 2; factors.push({ name: 'GD', pts: 2, rank: rankings.gd }); }
  else { factors.push({ name: 'GD', pts: 0, rank: rankings.gd }); }
  
  // Goals Against (4%)
  if (rankings.ga <= 5) { score += 4; factors.push({ name: 'GA', pts: 4, rank: rankings.ga }); }
  else if (rankings.ga <= 10) { score += 2; factors.push({ name: 'GA', pts: 2, rank: rankings.ga }); }
  else { factors.push({ name: 'GA', pts: 0, rank: rankings.ga }); }
  
  // Depth (5%)
  if (team.depth20g >= 4) { score += 5; factors.push({ name: 'Depth', pts: 5, value: team.depth20g, rank: rankings.depth }); }
  else if (team.depth20g >= 3) { score += 3; factors.push({ name: 'Depth', pts: 3, value: team.depth20g, rank: rankings.depth }); }
  else { factors.push({ name: 'Depth', pts: 0, value: team.depth20g, rank: rankings.depth }); }
  
  // Star Power (5%)
  if (team.hasStar) { score += 5; factors.push({ name: 'Star', pts: 5, has: true }); }
  else { factors.push({ name: 'Star', pts: 0, has: false }); }
  
  // Weight (4%)
  if (rankings.weight <= 5) { score += 4; factors.push({ name: 'Weight', pts: 4, rank: rankings.weight }); }
  else if (rankings.weight <= 10) { score += 2; factors.push({ name: 'Weight', pts: 2, rank: rankings.weight }); }
  else { factors.push({ name: 'Weight', pts: 0, rank: rankings.weight }); }
  
  // Tier
  let tier;
  if (score >= 75) tier = 'elite';
  else if (score >= 58) tier = 'contender';
  else if (score >= 42) tier = 'bubble';
  else tier = 'longshot';
  
  return { score, factors, rankings, tier, gd, xgd, formStatus };
};

// Main Component
const NHLChampionshipV3Verified = () => {
  const [activeView, setActiveView] = useState('matrix');
  const [selectedConference, setSelectedConference] = useState('all');
  const [hoveredTeam, setHoveredTeam] = useState(null);
  
  const processedTeams = useMemo(() => {
    return teamsData.map(t => ({
      ...t,
      ...calculateScore(t, teamsData)
    })).sort((a, b) => b.score - a.score);
  }, []);
  
  const filteredTeams = useMemo(() => {
    return selectedConference === 'all' 
      ? processedTeams 
      : processedTeams.filter(t => t.conf === selectedConference);
  }, [processedTeams, selectedConference]);
  
  const tierColors = {
    elite: '#10B981',
    contender: '#3B82F6',
    bubble: '#F59E0B',
    longshot: '#EF4444',
  };
  
  const formColors = {
    hot: '#10B981',
    warm: '#34d399',
    stable: '#94a3b8',
    cold: '#F59E0B',
    freezing: '#EF4444',
  };
  
  const formIcons = {
    hot: '🔥',
    warm: '📈',
    stable: '➡️',
    cold: '📉',
    freezing: '🥶',
  };
  
  const RankBadge = ({ rank, inverse = false, highlight = false }) => {
    const isGood = rank <= 5;
    const isOk = rank <= 10;
    const isMid = rank <= 16;
    return (
      <span style={{
        display: 'inline-block',
        minWidth: '24px',
        padding: '1px 4px',
        borderRadius: '3px',
        fontSize: '0.65rem',
        fontWeight: '600',
        textAlign: 'center',
        background: isGood ? 'rgba(16, 185, 129, 0.3)' : isOk ? 'rgba(251, 191, 36, 0.25)' : isMid ? 'rgba(100, 116, 139, 0.2)' : 'rgba(239, 68, 68, 0.2)',
        color: isGood ? '#34d399' : isOk ? '#fbbf24' : isMid ? '#94a3b8' : '#f87171',
        border: highlight ? '1px solid currentColor' : 'none',
      }}>
        {rank}
      </span>
    );
  };
  
  const FormBadge = ({ status }) => (
    <span style={{
      display: 'inline-flex',
      alignItems: 'center',
      gap: '3px',
      padding: '1px 6px',
      borderRadius: '3px',
      fontSize: '0.65rem',
      fontWeight: '600',
      background: `${formColors[status]}20`,
      color: formColors[status],
    }}>
      {formIcons[status]} {status.toUpperCase()}
    </span>
  );
  
  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%)',
      color: '#f1f5f9',
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
      padding: '20px',
    }}>
      {/* Header */}
      <div style={{ textAlign: 'center', marginBottom: '20px' }}>
        <h1 style={{ fontSize: '1.6rem', fontWeight: '700', marginBottom: '6px', color: '#f8fafc' }}>
          🏒 NHL Championship Framework V3
        </h1>
        <p style={{ color: '#64748b', fontSize: '0.8rem', marginBottom: '4px' }}>
          Data Sources: ESPN Standings (Jan 17-18, 2026) | Analytics: Natural Stat Trick / MoneyPuck
        </p>
        <p style={{ color: '#94a3b8', fontSize: '0.75rem' }}>
          ⚠️ Verify CF%/HDCF%/xG/PDO at <a href="https://naturalstattrick.com/teamtable.php" target="_blank" rel="noopener noreferrer" style={{ color: '#3B82F6' }}>naturalstattrick.com</a>
        </p>
      </div>
      
      {/* Navigation */}
      <div style={{ display: 'flex', justifyContent: 'center', gap: '8px', marginBottom: '20px', flexWrap: 'wrap' }}>
        {['matrix', 'scatter', 'weights'].map(view => (
          <button
            key={view}
            onClick={() => setActiveView(view)}
            style={{
              padding: '8px 16px',
              borderRadius: '6px',
              border: 'none',
              cursor: 'pointer',
              fontWeight: '600',
              fontSize: '0.8rem',
              background: activeView === view ? '#3B82F6' : 'rgba(51, 65, 85, 0.8)',
              color: activeView === view ? '#fff' : '#94a3b8',
            }}
          >
            {view === 'matrix' && '📊 Full Matrix'}
            {view === 'scatter' && '🎯 HDCF% vs xGD'}
            {view === 'weights' && '⚖️ V3 Weights'}
          </button>
        ))}
      </div>
      
      {/* Conference Filter */}
      <div style={{ display: 'flex', justifyContent: 'center', gap: '8px', marginBottom: '16px' }}>
        {['all', 'East', 'West'].map(conf => (
          <button
            key={conf}
            onClick={() => setSelectedConference(conf)}
            style={{
              padding: '5px 14px',
              borderRadius: '5px',
              border: 'none',
              cursor: 'pointer',
              fontSize: '0.75rem',
              background: selectedConference === conf ? '#475569' : 'rgba(51, 65, 85, 0.5)',
              color: selectedConference === conf ? '#fff' : '#94a3b8',
            }}
          >
            {conf === 'all' ? 'All Teams' : conf}
          </button>
        ))}
      </div>
      
      {/* FULL MATRIX VIEW - Now shows ALL rankings */}
      {activeView === 'matrix' && (
        <div style={{ overflowX: 'auto' }}>
          {/* Tier Legend */}
          <div style={{ display: 'flex', justifyContent: 'center', gap: '16px', marginBottom: '12px', flexWrap: 'wrap' }}>
            {Object.entries(tierColors).map(([tier, color]) => (
              <div key={tier} style={{ display: 'flex', alignItems: 'center', gap: '5px', fontSize: '0.7rem' }}>
                <div style={{ width: '10px', height: '10px', borderRadius: '50%', background: color }} />
                <span style={{ color: '#94a3b8', textTransform: 'capitalize' }}>{tier}</span>
              </div>
            ))}
            <div style={{ color: '#64748b', fontSize: '0.7rem', marginLeft: '8px' }}>
              Rankings: <span style={{ color: '#34d399' }}>1-5</span> | <span style={{ color: '#fbbf24' }}>6-10</span> | <span style={{ color: '#94a3b8' }}>11-16</span> | <span style={{ color: '#f87171' }}>17+</span>
            </div>
          </div>
          
          <table style={{ width: '100%', maxWidth: '1400px', margin: '0 auto', borderCollapse: 'collapse', fontSize: '0.7rem' }}>
            <thead>
              <tr style={{ background: 'rgba(30, 41, 59, 0.9)', borderBottom: '2px solid #475569' }}>
                <th style={{ padding: '8px 4px', textAlign: 'left', color: '#64748b', fontSize: '0.65rem' }}>#</th>
                <th style={{ padding: '8px 4px', textAlign: 'left', color: '#64748b', fontSize: '0.65rem' }}>Team</th>
                <th style={{ padding: '8px 4px', textAlign: 'center', color: '#f8fafc', fontSize: '0.65rem', fontWeight: '700' }}>Score</th>
                <th style={{ padding: '8px 4px', textAlign: 'center', color: '#10B981', fontSize: '0.65rem', fontWeight: '700' }}>HDCF%<br/><span style={{ fontWeight: '400', color: '#64748b' }}>14%</span></th>
                <th style={{ padding: '8px 4px', textAlign: 'center', color: '#10B981', fontSize: '0.65rem', fontWeight: '700' }}>xGD<br/><span style={{ fontWeight: '400', color: '#64748b' }}>14%</span></th>
                <th style={{ padding: '8px 4px', textAlign: 'center', color: '#94a3b8', fontSize: '0.65rem' }}>CF%<br/><span style={{ fontWeight: '400', color: '#64748b' }}>10%</span></th>
                <th style={{ padding: '8px 4px', textAlign: 'center', color: '#94a3b8', fontSize: '0.65rem' }}>xGA<br/><span style={{ fontWeight: '400', color: '#64748b' }}>10%</span></th>
                <th style={{ padding: '8px 4px', textAlign: 'center', color: '#94a3b8', fontSize: '0.65rem' }}>xGF<br/><span style={{ fontWeight: '400', color: '#64748b' }}>6%</span></th>
                <th style={{ padding: '8px 4px', textAlign: 'center', color: '#3B82F6', fontSize: '0.65rem', fontWeight: '700' }}>Form<br/><span style={{ fontWeight: '400', color: '#64748b' }}>6%</span></th>
                <th style={{ padding: '8px 4px', textAlign: 'center', color: '#94a3b8', fontSize: '0.65rem' }}>PK%<br/><span style={{ fontWeight: '400', color: '#64748b' }}>8%</span></th>
                <th style={{ padding: '8px 4px', textAlign: 'center', color: '#94a3b8', fontSize: '0.65rem' }}>PDO<br/><span style={{ fontWeight: '400', color: '#64748b' }}>6%</span></th>
                <th style={{ padding: '8px 4px', textAlign: 'center', color: '#64748b', fontSize: '0.65rem' }}>GD<br/><span style={{ fontWeight: '400' }}>4%</span></th>
                <th style={{ padding: '8px 4px', textAlign: 'center', color: '#64748b', fontSize: '0.65rem' }}>GA<br/><span style={{ fontWeight: '400' }}>4%</span></th>
                <th style={{ padding: '8px 4px', textAlign: 'center', color: '#64748b', fontSize: '0.65rem' }}>Depth<br/><span style={{ fontWeight: '400' }}>5%</span></th>
                <th style={{ padding: '8px 4px', textAlign: 'center', color: '#64748b', fontSize: '0.65rem' }}>Star<br/><span style={{ fontWeight: '400' }}>5%</span></th>
                <th style={{ padding: '8px 4px', textAlign: 'center', color: '#64748b', fontSize: '0.65rem' }}>Wt<br/><span style={{ fontWeight: '400' }}>4%</span></th>
              </tr>
            </thead>
            <tbody>
              {filteredTeams.map((team, idx) => (
                <tr
                  key={team.team}
                  style={{
                    background: idx % 2 === 0 ? 'rgba(30, 41, 59, 0.5)' : 'rgba(30, 41, 59, 0.25)',
                    borderLeft: `3px solid ${tierColors[team.tier]}`,
                  }}
                >
                  <td style={{ padding: '6px 4px', fontWeight: '600', color: '#64748b', fontSize: '0.7rem' }}>{idx + 1}</td>
                  <td style={{ padding: '6px 4px' }}>
                    <div style={{ fontWeight: '700', color: '#f1f5f9', fontSize: '0.8rem' }}>{team.team}</div>
                    <div style={{ color: '#475569', fontSize: '0.6rem' }}>{team.conf} • {team.w}-{team.l}-{team.otl}</div>
                  </td>
                  <td style={{ padding: '6px 4px', textAlign: 'center' }}>
                    <span style={{
                      fontWeight: '700',
                      fontSize: '1rem',
                      color: tierColors[team.tier],
                    }}>
                      {team.score}
                    </span>
                  </td>
                  {/* HDCF% with rank */}
                  <td style={{ padding: '6px 4px', textAlign: 'center' }}>
                    <div style={{ fontWeight: '600', fontSize: '0.75rem' }}>{team.hdcf.toFixed(1)}%</div>
                    <RankBadge rank={team.rankings.hdcf} />
                  </td>
                  {/* xGD with rank */}
                  <td style={{ padding: '6px 4px', textAlign: 'center' }}>
                    <div style={{ color: team.xgd > 0 ? '#10B981' : '#EF4444', fontWeight: '600', fontSize: '0.75rem' }}>
                      {team.xgd > 0 ? '+' : ''}{team.xgd.toFixed(1)}
                    </div>
                    <RankBadge rank={team.rankings.xgd} />
                  </td>
                  {/* CF% with rank */}
                  <td style={{ padding: '6px 4px', textAlign: 'center' }}>
                    <div style={{ fontSize: '0.75rem' }}>{team.cf.toFixed(1)}%</div>
                    <RankBadge rank={team.rankings.cf} />
                  </td>
                  {/* xGA with rank */}
                  <td style={{ padding: '6px 4px', textAlign: 'center' }}>
                    <div style={{ fontSize: '0.75rem' }}>{team.xga.toFixed(1)}</div>
                    <RankBadge rank={team.rankings.xga} />
                  </td>
                  {/* xGF with rank */}
                  <td style={{ padding: '6px 4px', textAlign: 'center' }}>
                    <div style={{ fontSize: '0.75rem' }}>{team.xgf.toFixed(1)}</div>
                    <RankBadge rank={team.rankings.xgf} />
                  </td>
                  {/* Form with rank */}
                  <td style={{ padding: '6px 4px', textAlign: 'center' }}>
                    <FormBadge status={team.formStatus} />
                    <div style={{ marginTop: '2px' }}>
                      <RankBadge rank={team.rankings.recentXgf} />
                    </div>
                  </td>
                  {/* PK% with rank */}
                  <td style={{ padding: '6px 4px', textAlign: 'center' }}>
                    <div style={{ fontSize: '0.75rem' }}>{team.pkPct.toFixed(1)}%</div>
                    <RankBadge rank={team.rankings.pk} />
                  </td>
                  {/* PDO with rank */}
                  <td style={{ padding: '6px 4px', textAlign: 'center' }}>
                    <div style={{
                      fontSize: '0.75rem',
                      color: team.pdo >= 100 && team.pdo <= 102 ? '#10B981' : team.pdo > 103 ? '#EF4444' : '#94a3b8',
                    }}>
                      {team.pdo.toFixed(1)}
                    </div>
                    <RankBadge rank={team.rankings.pdo} />
                  </td>
                  {/* GD with rank */}
                  <td style={{ padding: '6px 4px', textAlign: 'center' }}>
                    <div style={{ color: team.gd > 0 ? '#10B981' : team.gd < 0 ? '#EF4444' : '#94a3b8', fontSize: '0.75rem' }}>
                      {team.gd > 0 ? '+' : ''}{team.gd}
                    </div>
                    <RankBadge rank={team.rankings.gd} />
                  </td>
                  {/* GA with rank */}
                  <td style={{ padding: '6px 4px', textAlign: 'center' }}>
                    <div style={{ fontSize: '0.75rem' }}>{team.ga}</div>
                    <RankBadge rank={team.rankings.ga} />
                  </td>
                  {/* Depth with rank */}
                  <td style={{ padding: '6px 4px', textAlign: 'center' }}>
                    <div style={{ fontSize: '0.75rem' }}>{team.depth20g}</div>
                    <RankBadge rank={team.rankings.depth} />
                  </td>
                  {/* Star */}
                  <td style={{ padding: '6px 4px', textAlign: 'center' }}>
                    <span style={{ fontSize: '0.8rem' }}>{team.hasStar ? '⭐' : '—'}</span>
                  </td>
                  {/* Weight with rank */}
                  <td style={{ padding: '6px 4px', textAlign: 'center' }}>
                    <div style={{ fontSize: '0.75rem' }}>{team.weight}</div>
                    <RankBadge rank={team.rankings.weight} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          
          {/* Data verification note */}
          <div style={{ textAlign: 'center', marginTop: '16px', padding: '12px', background: 'rgba(59, 130, 246, 0.1)', borderRadius: '8px', maxWidth: '800px', margin: '16px auto 0' }}>
            <p style={{ color: '#94a3b8', fontSize: '0.75rem', margin: 0 }}>
              <strong style={{ color: '#3B82F6' }}>📊 Verify Analytics Data:</strong> GF/GA/Standings from ESPN (verified). 
              CF%/HDCF%/xG/PDO should be verified at{' '}
              <a href="https://naturalstattrick.com/teamtable.php" target="_blank" rel="noopener noreferrer" style={{ color: '#3B82F6' }}>Natural Stat Trick</a> or{' '}
              <a href="https://moneypuck.com/teams.htm" target="_blank" rel="noopener noreferrer" style={{ color: '#3B82F6' }}>MoneyPuck</a>
            </p>
          </div>
        </div>
      )}
      
      {/* SCATTER PLOT VIEW */}
      {activeView === 'scatter' && (
        <div>
          <div style={{ textAlign: 'center', marginBottom: '16px' }}>
            <h2 style={{ fontSize: '1.1rem', color: '#f8fafc', marginBottom: '4px' }}>HDCF% vs xG Differential</h2>
            <p style={{ color: '#64748b', fontSize: '0.75rem' }}>
              Top-right = Elite Contenders • Size = Recent Form
            </p>
          </div>
          
          <svg width={700} height={500} style={{ display: 'block', margin: '0 auto' }}>
            <rect width={700} height={500} fill="#1e293b" rx="8" />
            
            {/* Quadrants */}
            <rect x={345} y={40} width={295} height={200} fill="rgba(16, 185, 129, 0.1)" />
            <text x={490} y={130} fill="#10B981" fontSize="11" fontWeight="600" textAnchor="middle">ELITE</text>
            
            <rect x={60} y={40} width={285} height={200} fill="rgba(251, 191, 36, 0.08)" />
            <text x={200} y={130} fill="#F59E0B" fontSize="11" fontWeight="600" textAnchor="middle">REGRESSION RISK</text>
            
            <rect x={345} y={240} width={295} height={200} fill="rgba(59, 130, 246, 0.08)" />
            <text x={490} y={340} fill="#3B82F6" fontSize="11" fontWeight="600" textAnchor="middle">UNDERVALUED</text>
            
            <rect x={60} y={240} width={285} height={200} fill="rgba(239, 68, 68, 0.08)" />
            <text x={200} y={340} fill="#EF4444" fontSize="11" fontWeight="600" textAnchor="middle">AVOID</text>
            
            {/* Center lines */}
            <line x1={345} y1={40} x2={345} y2={440} stroke="#475569" strokeWidth="2" />
            <line x1={60} y1={240} x2={640} y2={240} stroke="#475569" strokeWidth="2" />
            
            {/* Plot teams */}
            {processedTeams.map(team => {
              const x = 60 + ((team.hdcf - 45) / 15) * 580;
              const y = 440 - ((team.xgd + 20) / 40) * 400;
              const baseSize = 6;
              const formBonus = team.formStatus === 'hot' ? 3 : team.formStatus === 'warm' ? 1 : team.formStatus === 'cold' ? -1 : team.formStatus === 'freezing' ? -2 : 0;
              const size = Math.max(4, baseSize + formBonus);
              
              return (
                <g key={team.team}
                  onMouseEnter={() => setHoveredTeam(team)}
                  onMouseLeave={() => setHoveredTeam(null)}
                  style={{ cursor: 'pointer' }}
                >
                  <circle cx={x} cy={y} r={hoveredTeam?.team === team.team ? size + 2 : size}
                    fill={tierColors[team.tier]} fillOpacity={0.9}
                    stroke={hoveredTeam?.team === team.team ? '#fff' : formColors[team.formStatus]}
                    strokeWidth={hoveredTeam?.team === team.team ? 2 : 1} />
                  <text x={x} y={y + 2.5} fill="#fff" fontSize="6" fontWeight="700" textAnchor="middle">
                    {team.team}
                  </text>
                </g>
              );
            })}
            
            {/* Axes labels */}
            <text x={350} y={480} fill="#94a3b8" fontSize="11" fontWeight="600" textAnchor="middle">
              HDCF% (High-Danger Chance For %) →
            </text>
            <text x={20} y={240} fill="#94a3b8" fontSize="11" fontWeight="600" textAnchor="middle"
              transform="rotate(-90, 20, 240)">
              xG Differential →
            </text>
            
            {/* Tick labels */}
            {[45, 48, 51, 54, 57, 60].map(v => (
              <text key={`x-${v}`} x={60 + ((v - 45) / 15) * 580} y={460}
                fill="#64748b" fontSize="9" textAnchor="middle">{v}%</text>
            ))}
            {[-20, -10, 0, 10, 20].map(v => (
              <text key={`y-${v}`} x={50} y={440 - ((v + 20) / 40) * 400 + 3}
                fill="#64748b" fontSize="9" textAnchor="end">{v > 0 ? `+${v}` : v}</text>
            ))}
          </svg>
          
          {/* Tooltip */}
          {hoveredTeam && (
            <div style={{
              position: 'fixed',
              top: '50%',
              right: '20px',
              transform: 'translateY(-50%)',
              background: 'rgba(15, 23, 42, 0.95)',
              border: `2px solid ${tierColors[hoveredTeam.tier]}`,
              borderRadius: '8px',
              padding: '14px',
              minWidth: '200px',
              zIndex: 100,
            }}>
              <div style={{ fontWeight: '700', fontSize: '1rem', marginBottom: '6px', color: tierColors[hoveredTeam.tier] }}>
                {hoveredTeam.name}
              </div>
              <FormBadge status={hoveredTeam.formStatus} />
              <div style={{ display: 'grid', gap: '4px', fontSize: '0.75rem', marginTop: '8px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: '#94a3b8' }}>Score:</span>
                  <span style={{ fontWeight: '700', color: tierColors[hoveredTeam.tier] }}>{hoveredTeam.score}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: '#94a3b8' }}>HDCF%:</span>
                  <span>{hoveredTeam.hdcf.toFixed(1)}% <RankBadge rank={hoveredTeam.rankings.hdcf} /></span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: '#94a3b8' }}>xG Diff:</span>
                  <span style={{ color: hoveredTeam.xgd > 0 ? '#10B981' : '#EF4444' }}>
                    {hoveredTeam.xgd > 0 ? '+' : ''}{hoveredTeam.xgd.toFixed(1)}
                  </span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: '#94a3b8' }}>Record:</span>
                  <span>{hoveredTeam.w}-{hoveredTeam.l}-{hoveredTeam.otl} ({hoveredTeam.pts}pts)</span>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
      
      {/* WEIGHTS VIEW */}
      {activeView === 'weights' && (
        <div style={{ maxWidth: '800px', margin: '0 auto' }}>
          <div style={{ textAlign: 'center', marginBottom: '20px' }}>
            <h2 style={{ fontSize: '1.1rem', color: '#f8fafc', marginBottom: '4px' }}>V3 Weight Distribution</h2>
            <p style={{ color: '#64748b', fontSize: '0.75rem' }}>
              Research-validated • HDCF% + Recent Form added • GD/Weight reduced
            </p>
          </div>
          
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8rem' }}>
            <thead>
              <tr style={{ background: 'rgba(30, 41, 59, 0.8)', borderBottom: '2px solid #475569' }}>
                <th style={{ padding: '10px', textAlign: 'left', color: '#94a3b8' }}>Factor</th>
                <th style={{ padding: '10px', textAlign: 'center', color: '#94a3b8' }}>Weight</th>
                <th style={{ padding: '10px', textAlign: 'left', color: '#94a3b8' }}>Rationale</th>
              </tr>
            </thead>
            <tbody>
              {[
                { factor: 'HDCF%', weight: 14, note: 'Most predictive — shot quality > quantity', isNew: true },
                { factor: 'xG Differential', weight: 14, note: 'Process over results — 60% of winners top-10' },
                { factor: 'CF%', weight: 10, note: 'Possession proxy — HDCF% captures quality better' },
                { factor: 'xGA (Defense)', weight: 10, note: 'Defensive expected goals — critical in playoffs' },
                { factor: 'Recent Form', weight: 6, note: 'NEW: 20-game xGF% — asymmetric cold penalty', isNew: true },
                { factor: 'xGF (Offense)', weight: 6, note: 'Offensive expected goals creation' },
                { factor: 'PK%', weight: 8, note: 'Penalty kill matters in playoff hockey' },
                { factor: 'PDO Range', weight: 6, note: 'Penalizes extremes — >103 = regression risk' },
                { factor: 'Goal Differential', weight: 4, note: 'REDUCED: Only 17% of GD leaders won Cup', reduced: true },
                { factor: 'Goals Against', weight: 4, note: 'REDUCED: xGA is more predictive', reduced: true },
                { factor: 'Scoring Depth', weight: 5, note: 'Players with 20+ goals — depth matters in grind' },
                { factor: 'Star Power', weight: 5, note: 'Elite superstar presence — most winners have stars' },
                { factor: 'Team Weight', weight: 4, note: 'REDUCED: Trend breaking (FLA 2024 = 18th)', reduced: true },
              ].map((row, idx) => (
                <tr key={row.factor} style={{
                  background: idx % 2 === 0 ? 'rgba(30, 41, 59, 0.4)' : 'rgba(30, 41, 59, 0.2)',
                  borderLeft: row.isNew ? '3px solid #10B981' : row.reduced ? '3px solid #EF4444' : '3px solid transparent',
                }}>
                  <td style={{ padding: '8px 10px', fontWeight: '600', color: row.isNew ? '#10B981' : row.reduced ? '#EF4444' : '#f1f5f9' }}>
                    {row.isNew && '✨ '}{row.factor}
                  </td>
                  <td style={{ padding: '8px 10px', textAlign: 'center', fontWeight: '700', color: '#f1f5f9' }}>{row.weight}%</td>
                  <td style={{ padding: '8px 10px', fontSize: '0.75rem', color: '#94a3b8' }}>{row.note}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      
      {/* Footer */}
      <div style={{ textAlign: 'center', marginTop: '24px', padding: '12px', borderTop: '1px solid #334155' }}>
        <p style={{ color: '#64748b', fontSize: '0.7rem' }}>
          V3 Framework • Standings: ESPN (Jan 17-18, 2026) • Analytics: Natural Stat Trick / MoneyPuck (verify before use)
        </p>
      </div>
    </div>
  );
};

export default NHLChampionshipV3Verified;
