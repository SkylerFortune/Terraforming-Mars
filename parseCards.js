import fs from 'fs';
import path from 'path';

// Recursively find all .ts files in a directory
function getAllTsFiles(dirPath, fileList = []) {
  const files = fs.readdirSync(dirPath);

  files.forEach((file) => {
    const fullPath = path.join(dirPath, file);
    if (fs.statSync(fullPath).isDirectory()) {
      getAllTsFiles(fullPath, fileList);
    } else if (file.endsWith('.ts') && !file.endsWith('.d.ts')) {
      fileList.push(fullPath);
    }
  });

  return fileList;
}

// Extract card data from TypeScript source code using Regex
function parseCardFile(code, fileName) {
  // Extract Class Name
  const classMatch = code.match(/export class (\w+)/);
  if (!classMatch) return null;

  const card = {
    className: classMatch[1],
    filePath: fileName,
  };

  // Extract cost: number = 9;
  const costMatch = code.match(/public cost:\s*number\s*=\s*(\d+);/);
  if (costMatch) {
    card.cost = Number(costMatch[1]);
  }

  // Extract cardType = CardType.EVENT;
  const typeMatch = code.match(/public cardType:\s*CardType\s*=\s*CardType\.(\w+);/);
  if (typeMatch) {
    card.cardType = typeMatch[1];
  }

  // Extract name = CardName.WATER_TO_VENUS;
  const nameMatch = code.match(/public name:\s*CardName\s*=\s*CardName\.(\w+);/);
  if (nameMatch) {
    card.name = nameMatch[1];
  }

  // Extract tags = [Tags.SPACE, Tags.SCIENCE];
  const tagsMatch = code.match(/public tags:\s*Array<Tags>\s*=\s*\[(.*?)\];/s);
  if (tagsMatch) {
    card.tags = tagsMatch[1]
      .split(',')
      .map((t) => t.trim().replace(/^Tags\./, ''))
      .filter(Boolean);
  } else {
    card.tags = [];
  }

  // Extract return value from getVictoryPoints()
  const vpMatch = code.match(/getVictoryPoints\(\)\s*\{[\s\S]*?return\s*(\d+);/);
  if (vpMatch) {
    card.victoryPoints = Number(vpMatch[1]);
  }

  // Extract return value from getRequirementBonus()
  const bonusMatch = code.match(/getRequirementBonus\(\)\s*\{[\s\S]*?return\s*(\d+);/);
  if (bonusMatch) {
    card.requirementBonus = Number(bonusMatch[1]);
  }

  return card;
}

// Execution
const cardsDirectory = './ts/cards'; // Update to your cards path
const filePaths = getAllTsFiles(cardsDirectory);

console.log(`Found ${filePaths.length} card files. Parsing with pure JS...`);

const allCards = [];

filePaths.forEach((filePath) => {
  try {
    const code = fs.readFileSync(filePath, 'utf-8');
    const cardData = parseCardFile(code, path.basename(filePath));
    if (cardData) {
      allCards.push(cardData);
    }
  } catch (err) {
    console.error(`Error reading ${filePath}:`, err);
  }
});

fs.writeFileSync('./assets/cards.json', JSON.stringify(allCards, null, 2));
console.log(`Successfully converted ${allCards.length} cards to cards.json!`);