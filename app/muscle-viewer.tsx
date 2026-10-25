import { Stack } from 'expo-router';
import { ModelViewerScreen } from '../src/features/model3d/ModelViewerScreen';
export default function MuscleViewerRoute() {
  return <><Stack.Screen options={{ gestureEnabled: false }} /><ModelViewerScreen /></>;
}
