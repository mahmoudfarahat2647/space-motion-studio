import fs from "fs";
import { RenderManifestSchema, StoryboardSchema } from "../types/contracts";

function main() {
  const args = process.argv.slice(2);
  if (args.length < 2) {
    console.error("Usage: tsx validate-manifest.ts <type: manifest|storyboard> <file_path>");
    process.exit(1);
  }

  const [type, filePath] = args;
  try {
    const raw = fs.readFileSync(filePath, "utf-8");
    const json = JSON.parse(raw);

    if (type === "manifest") {
      RenderManifestSchema.parse(json);
      console.log(`Manifest validation succeeded for: ${filePath}`);
    } else if (type === "storyboard") {
      StoryboardSchema.parse(json);
      console.log(`Storyboard validation succeeded for: ${filePath}`);
    } else {
      console.error(`Unknown contract type: ${type}`);
      process.exit(1);
    }
    process.exit(0);
  } catch (err: any) {
    console.error("Validation error:", err.message || err);
    process.exit(1);
  }
}

main();
