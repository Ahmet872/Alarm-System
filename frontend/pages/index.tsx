import { NextPage } from 'next'
import AlarmForm from '../components/AlarmForm'
import Head from 'next/head'

const Home: NextPage = () => {
  return (
    <div className="min-h-screen bg-gray-100">
      <Head>
        <title>Financial One-shot Alarm System</title>
        <meta name="description" content="Set one-time financial alarms" />
      </Head>

      <main className="container mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold text-center mb-8">
          Financial One-shot Alarm System
        </h1>
        <div className="max-w-2xl mx-auto">
          <AlarmForm />
        </div>
      </main>
    </div>
  )
}

export default Home