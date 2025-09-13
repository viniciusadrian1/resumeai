import React, { useRef, useState } from 'react'

export default function ResumeAI(){
  const [file, setFile] = useState(null)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const inputRef = useRef()

  const onFile = (e)=>{
    const f = e.target.files?.[0]
    if(!f) return
    if(!f.type.startsWith('audio/')){ setError('Por favor selecione um arquivo de áudio'); return }
    setFile(f); setError(''); setResult(null)
  }

  const upload = async ()=>{
    if(!file){ setError('Selecione um arquivo'); return }
    setLoading(true); setError(''); setResult(null)
    const fd = new FormData(); fd.append('file', file)
    try{
      const resp = await fetch('/api/upload-audio', { method: 'POST', body: fd })
      if(!resp.ok){
        const d = await resp.json().catch(()=>({detail: resp.statusText}))
        throw new Error(d.detail || 'Erro no servidor')
      }
      const json = await resp.json()
      setResult(json)
    }catch(err){
      setError(err.message || 'Erro desconhecido')
    }finally{
      setLoading(false)
    }
  }

  return (
    <div style={{maxWidth:900, margin:'24px auto', padding:18}}>
      <h1>ResumeAI</h1>
      <p>Envie um áudio de reunião e receba transcrição, resumo e insights.</p>

      <div style={{display:'flex', justifyContent:'space-between', alignItems:'center', gap:12}}>
        <div>
          <div style={{fontWeight:600}}>{file?file.name:'Nenhum arquivo selecionado'}</div>
          <div style={{color:'#666'}}>{file?Math.round(file.size/1024/1024*10)/10+' MB':'Formatos: mp3, wav, m4a'}</div>
        </div>
        <div style={{display:'flex', gap:8}}>
          <input ref={inputRef} onChange={onFile} type="file" accept="audio/*" style={{display:'none'}} />
          <button onClick={()=>inputRef.current?.click()} className='btn'>Selecionar</button>
          <button onClick={upload} disabled={loading||!file} className='btn'>{loading?'Processando...':'Enviar e Analisar'}</button>
        </div>
      </div>

      {error && <div style={{marginTop:12, color:'crimson'}}>{error}</div>}

      {result && (
        <div style={{marginTop:16}}>
          <h3>Resumo</h3>
          <div style={{whiteSpace:'pre-wrap'}}>{result.summary}</div>

          <h3 style={{marginTop:12}}>Transcrição</h3>
          <pre style={{background:'#f8f8f8', padding:10}}>{result.transcription}</pre>

          <h3 style={{marginTop:12}}>Insights</h3>
          <div>
            {result.insights?.map((ins,i)=>(
              <div key={i} style={{padding:8, borderBottom:'1px solid #eee'}}>
                <strong>{ins.title}</strong> <small>[{ins.type}]</small>
                <div style={{color:'#666'}}>{ins.description}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
