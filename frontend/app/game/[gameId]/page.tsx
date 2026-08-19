import GameBoard from "@/components/GameBoard";

export default async function GamePage({
  params,
}: {
  params: Promise<{ gameId: string }>;
}) {
  const { gameId } = await params;
  return <GameBoard gameId={gameId} />;
}
