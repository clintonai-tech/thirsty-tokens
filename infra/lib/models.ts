import { readFileSync } from 'node:fs';
import * as path from 'node:path';
import { parse } from 'yaml';

export interface BedrockModel {
  /** Inference profile ID, e.g. eu.amazon.nova-micro-v1:0 */
  readonly profileId: string;
  /** Foundation model ID the profile routes to, e.g. amazon.nova-micro-v1:0 */
  readonly foundationModelId: string;
}

interface RegistryFile {
  models: { litellm_model: string }[];
}

/** Reads backend/models.yaml so the registry stays the single source of truth for model IDs. */
export function loadBedrockModels(
  file = path.resolve(__dirname, '../../backend/models.yaml'),
): BedrockModel[] {
  const registry = parse(readFileSync(file, 'utf8')) as RegistryFile;
  return registry.models.map(({ litellm_model }) => {
    const profileId = litellm_model.replace(/^bedrock\//, '');
    return { profileId, foundationModelId: profileId.replace(/^eu\./, '') };
  });
}
