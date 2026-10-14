import { Redirect } from 'expo-router';

/** Keep existing /programs deep links while both universes share a vertical pager. */
export default function ProgramsRedirect() {
  return <Redirect href={{ pathname: '/', params: { universe: 'musculation' } }} />;
}
