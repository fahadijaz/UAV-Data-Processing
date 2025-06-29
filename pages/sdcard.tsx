import Head from "next/head";
import SDCardList from "@/components/SDCardList";

export default function Home() {
  return (
    <>
      <Head>
        <title>SD Card File Manager</title>
      </Head>
      <main className="max-w-2xl mx-auto mt-10">
        <h1 className="text-2xl font-bold mb-4">Drone SD Card Reader</h1>
        <SDCardList />
      </main>
    </>
  );
}
