import {useEffect,useMemo,useState} from 'react'
import {Link,useNavigate,useParams} from 'react-router-dom'
import PageHeader from '../components/PageHeader'
import Card from '../components/Card'
import Button from '../components/Button'
import DisclaimerBanner from '../components/DisclaimerBanner'
import DocumentForm from '../components/DocumentForm'
import {deleteDocument,getDocument,getDocumentTemplate,updateDocument} from '../services/documentService'
import type {DocumentDraft} from '../types/document'
import {ApiError} from '../services/apiClient'
import './pages.css'
import './CreateDocument.css'
import './DocumentDetails.css'

function DocumentDetails(){
 const{id}=useParams<{id:string}>(),navigate=useNavigate()
 const[document,setDocument]=useState<DocumentDraft|null>(null),[values,setValues]=useState<Record<string,string>>({}),[title,setTitle]=useState(''),[initialSnapshot,setInitialSnapshot]=useState(''),[isLoading,setIsLoading]=useState(true),[isSaving,setIsSaving]=useState(false),[isDeleting,setIsDeleting]=useState(false),[errorStatus,setErrorStatus]=useState<number|null>(null),[errorMessage,setErrorMessage]=useState<string|null>(null),[savedMessage,setSavedMessage]=useState<string|null>(null),[fieldErrors,setFieldErrors]=useState<Record<string,string>>({})
 const template=useMemo(()=>document?getDocumentTemplate(document.type):null,[document])
 const snapshot=useMemo(()=>JSON.stringify({title:title.trim(),values}),[title,values]),isDirty=document!==null&&snapshot!==initialSnapshot
 useEffect(()=>{if(!isDirty)return;const handler=(event:BeforeUnloadEvent)=>event.preventDefault();window.addEventListener('beforeunload',handler);return()=>window.removeEventListener('beforeunload',handler)},[isDirty])
 useEffect(()=>{let active=true;if(!id){setIsLoading(false);setErrorStatus(404);return}async function load(){setIsLoading(true);try{const data=await getDocument(id);if(!active)return;setDocument(data);setTitle(data.title);setValues(data.values);setInitialSnapshot(JSON.stringify({title:data.title,values:data.values}))}catch(error){if(!active)return;if(error instanceof ApiError){setErrorStatus(error.status);setErrorMessage(error.detail)}else{setErrorStatus(500);setErrorMessage('An unexpected error occurred while loading the document.')}}finally{if(active)setIsLoading(false)}}void load();return()=>{active=false}},[id])
 function change(name:string,value:string){setValues(prev=>({...prev,[name]:value}));setFieldErrors(prev=>{if(!prev[name])return prev;const next={...prev};delete next[name];return next});setSavedMessage(null)}
 function validate(){if(!template)return false;const next:Record<string,string>={};if(!title.trim())next.title='Document title is required.';for(const field of template.fields){const value=(values[field.name]??'').trim();if(field.required&&!value)next[field.name]=field.label+' is required.';if(field.type==='number'&&value&&!Number.isFinite(Number(value)))next[field.name]='Enter a valid number.';if(field.type==='date'&&value&&Number.isNaN(Date.parse(value)))next[field.name]='Enter a valid date.'}setFieldErrors(next);return Object.keys(next).length===0}
 async function save(){if(!id||!document||!validate())return;setIsSaving(true);setErrorMessage(null);setSavedMessage(null);try{const updated=await updateDocument(id,{title:title.trim(),details:values});setDocument(updated);setTitle(updated.title);setValues(updated.values);setInitialSnapshot(JSON.stringify({title:updated.title,values:updated.values}));setSavedMessage('Document saved successfully.')}catch(error){setErrorMessage(error instanceof Error?error.message:'Could not save the document.')}finally{setIsSaving(false)}}
 async function remove(){if(!id||isDeleting)return;if(!window.confirm('Delete this document permanently? This action cannot be undone.'))return;setIsDeleting(true);setErrorMessage(null);try{await deleteDocument(id);navigate('/app/documents',{replace:true})}catch(error){setErrorMessage(error instanceof Error?error.message:'Could not delete the document.');setIsDeleting(false)}}
 if(isLoading)return <div className="page-container"><PageHeader title="Document" description="Loading your document..."/><Card title="Loading document" description="Retrieving document data securely."><p>Please wait...</p></Card></div>
 if(errorStatus===404||!document||!template)return <div className="page-container"><PageHeader title="Document" description="Manage your document."/><Card title="Document not found" description="The requested document does not exist or belongs to another account."><Link className="btn btn-secondary" to="/app/documents">Back to Documents</Link></Card></div>
 return <div className="page-container"><PageHeader title={document.title} description="Edit and manage your saved legal document."/>
 {errorMessage?<div className="alert alert-error" role="alert"><p>{errorMessage}</p></div>:null}{savedMessage?<div className="alert alert-success" role="status"><p>{savedMessage}</p></div>:null}
 <div className="detail-stack"><Card title="Document details" description={isDirty?'You have unsaved changes.':('Last updated '+new Date(document.updatedDate).toLocaleString())}>
 <div className="auth-form-field"><label htmlFor="document-title">Document title</label><input id="document-title" className="document-form-input" value={title} maxLength={255} aria-invalid={Boolean(fieldErrors.title)} onChange={e=>{setTitle(e.target.value);setSavedMessage(null)}}/>{fieldErrors.title?<p className="field-error" role="alert">{fieldErrors.title}</p>:null}</div>
 <DocumentForm template={template} values={values} errors={fieldErrors} onChange={change}/>
 <div className="detail-actions"><Button disabled={isSaving||isDeleting||!isDirty} onClick={save}>{isSaving?'Saving...':'Save Changes'}</Button><Button variant="secondary" disabled={isSaving||isDeleting} onClick={()=>navigate('/app/documents')}>Back</Button><Button variant="danger" disabled={isSaving||isDeleting} onClick={remove}>{isDeleting?'Deleting...':'Delete Document'}</Button></div></Card>
 <Card title="Document status" description="This document is stored in your authenticated workspace."><div className="detail-meta"><div><p className="detail-meta-label">Type</p><p className="detail-meta-value">{template.title}</p></div><div><p className="detail-meta-label">Status</p><p className="detail-meta-value">{document.status}</p></div><div><p className="detail-meta-label">Created</p><p className="detail-meta-value">{new Date(document.createdDate).toLocaleString()}</p></div><div><p className="detail-meta-label">Updated</p><p className="detail-meta-value">{new Date(document.updatedDate).toLocaleString()}</p></div></div></Card>
 <DisclaimerBanner/></div></div>
}
export default DocumentDetails
