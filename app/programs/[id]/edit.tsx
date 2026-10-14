import { useLocalSearchParams } from 'expo-router';

import { ProgramEditor } from '../../../src/features/programs/ProgramEditor';
import { routeId } from '../../../src/features/programs/shared';

export default function EditProgramScreen() {
  const params = useLocalSearchParams<{ id: string }>();
  return <ProgramEditor mode="edit" id={routeId(params.id)} />;
}
