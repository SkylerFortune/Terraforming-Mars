import fs from 'fs';
import path from 'path';

// Recursively find all .ts files and capture their subfolder (expansion)
function getAllCardFiles(dirPath) {
  const fileRecords = [];

  function walk(currentDir) {
    const files = fs.readdirSync(currentDir);

    files.forEach((file) => {
      const fullPath = path.join(currentDir, file);
      const stat = fs.statSync(fullPath);

      if (stat.isDirectory()) {
        walk(fullPath);
      } else if (file.endsWith('.ts') && !file.endsWith('.d.ts')) {
        // Determine expansion from relative folder path
        const relativeDir = path.relative(dirPath, currentDir);
        // If the file is directly in the root cards folder, label it 'base'
        const expansion = relativeDir ? relativeDir.split(path.sep)[0] : 'base';

        fileRecords.push({ fullPath, expansion, fileName: file });
      }
    });
  }

  walk(dirPath);
  return fileRecords;
}

// Extract card data from TypeScript source code using Regex
function parseCardFile(code, fileName, expansion) {
  const classMatch = code.match(/export class (\w+)/);
  if (!classMatch) return null;

  const card = {
    className: classMatch[1],
    expansion: expansion,
    filePath: fileName,
  };

  const costMatch = code.match(/public cost:\s*number\s*=\s*(\d+);/);
  if (costMatch) card.cost = Number(costMatch[1]);

  const typeMatch = code.match(/public cardType:\s*CardType\s*=\s*CardType\.(\w+);/);
  if (typeMatch) card.cardType = typeMatch[1];

  const nameMatch = code.match(/public name:\s*CardName\s*=\s*CardName\.(\w+);/);
  if (nameMatch) card.name = nameMatch[1];

  const tagsMatch = code.match(/public tags:\s*Array<Tags>\s*=\s*\[(.*?)\];/s);
  if (tagsMatch) {
    card.tags = tagsMatch[1]
      .split(',')
      .map((t) => t.trim().replace(/^Tags\./, ''))
      .filter(Boolean);
  } else {
    card.tags = [];
  }

  const vpMatch = code.match(/getVictoryPoints\(\)\s*\{[\s\S]*?return\s*(\d+);/);
  if (vpMatch) card.victoryPoints = Number(vpMatch[1]);

  const bonusMatch = code.match(/getRequirementBonus\(\)\s*\{[\s\S]*?return\s*(\d+);/);
  if (bonusMatch) card.requirementBonus = Number(bonusMatch[1]);

  return card;
}

// Execution
const cardsDirectory = './ts/cards'; // Directory containing card subfolders
const outputDirectory = './json_cards'; // Output directory for split JSON files

// Ensure output directory exists
if (!fs.existsSync(outputDirectory)) {
  fs.mkdirSync(outputDirectory, { recursive: true });
}

const cardRecords = getAllCardFiles(cardsDirectory);
console.log(`Found ${cardRecords.length} card files across subfolders. Parsing...`);

// Map to hold array of cards for each expansion
const cardsByExpansion = {};

cardRecords.forEach(({ fullPath, expansion, fileName }) => {
  try {
    const code = fs.readFileSync(fullPath, 'utf-8');
    const cardData = parseCardFile(code, fileName, expansion);

    if (cardData) {
      if (!cardsByExpansion[expansion]) {
        cardsByExpansion[expansion] = [];
      }
      cardsByExpansion[expansion].push(cardData);
    }
  } catch (err) {
    console.error(`Error reading ${fullPath}:`, err);
  }
});

// Save each expansion array into its own JSON file
Object.entries(cardsByExpansion).forEach(([expansionName, cards]) => {
  const outputPath = path.join(outputDirectory, `${expansionName}.json`);
  fs.writeFileSync(outputPath, JSON.stringify(cards, null, 2));
  console.log(`Saved ${cards.length} cards to ${outputPath}`);
});