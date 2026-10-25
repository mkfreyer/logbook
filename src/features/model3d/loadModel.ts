import { Asset } from 'expo-asset';
import { File } from 'expo-file-system';
import { MODEL } from './model';

export async function loadModelBase64(): Promise<string> {
  const asset = Asset.fromModule(require('../../../assets/models/meshy-e45e5d8.glb'));
  await asset.downloadAsync();
  if (!asset.localUri) throw new Error('Le mannequin local est indisponible.');
  const file = new File(asset.localUri);
  if (file.size !== MODEL.bytes) throw new Error('Le fichier du mannequin est incomplet.');
  return file.base64();
}
