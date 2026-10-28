import { Asset } from 'expo-asset';
import { File } from 'expo-file-system';
import { SELECTION_MODEL } from './generated/selectionData';

export async function loadModelBase64(): Promise<string> {
  const asset = Asset.fromModule(require('../../../assets/models/meshy-m4d-uv.glb'));
  await asset.downloadAsync();
  if (!asset.localUri) throw new Error('Le mannequin local est indisponible.');
  const file = new File(asset.localUri);
  if (file.size !== SELECTION_MODEL.bytes) throw new Error('Le fichier du mannequin est incomplet.');
  return file.base64();
}
