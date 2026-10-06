import { apiRequest } from './apiClient'
import { TEMPLATE_FORM_SCHEMAS, type DocumentDraft, type DocumentDraftRequest, type DocumentDraftResponse, type DocumentTemplate, type DocumentTemplateResponse, type DocumentType, type DocumentUpdateRequest } from '../types/document'

function mapDocumentResponse(dto:DocumentDraftResponse):DocumentDraft{
  return {id:dto.document_id,type:dto.type,title:dto.title,createdDate:dto.created_date,updatedDate:dto.updated_date,status:dto.status,values:dto.details||{}}
}
export async function getDocumentTemplates():Promise<DocumentTemplate[]>{
  const dtos=await apiRequest<DocumentTemplateResponse[]>('/documents/templates')
  return dtos.map(dto=>{const schema=TEMPLATE_FORM_SCHEMAS[dto.type]||{fields:[],sections:[]};return{type:dto.type,title:dto.title,description:dto.description,category:dto.category,fields:schema.fields,sections:schema.sections}})
}
export function getDocumentTemplate(type:DocumentType,templates?:DocumentTemplate[]):DocumentTemplate{
  const match=templates?.find(item=>item.type===type);if(match)return match
  const metadata:Record<DocumentType,{title:string;description:string;category:string}>={
    rental:{title:'Rental Agreement',description:'Create a structured rental agreement from tenancy details.',category:'Tenancy'},
    employment:{title:'Employment Agreement',description:'Prepare a structured employment agreement from employment details.',category:'Employment'},
    nda:{title:'Non-Disclosure Agreement',description:'Create a structured NDA from confidentiality requirements.',category:'Confidentiality'},
    will:{title:'Will / Testament',description:'Organize information for a will or testament draft.',category:'Estate'}}
  const schema=TEMPLATE_FORM_SCHEMAS[type]||{fields:[],sections:[]};return{type,...metadata[type],fields:schema.fields,sections:schema.sections}
}
export async function getDocuments():Promise<DocumentDraft[]>{const dtos=await apiRequest<DocumentDraftResponse[]>('/documents');return dtos.map(mapDocumentResponse)}
export async function getDocument(id:string):Promise<DocumentDraft>{const dto=await apiRequest<DocumentDraftResponse>('/documents/'+encodeURIComponent(id));return mapDocumentResponse(dto)}
export async function createDraft(type:DocumentType,values:Record<string,string>):Promise<DocumentDraft>{const payload:DocumentDraftRequest={type,details:values};const dto=await apiRequest<DocumentDraftResponse>('/documents',{method:'POST',body:JSON.stringify(payload)});return mapDocumentResponse(dto)}
export async function updateDocument(id:string,payload:DocumentUpdateRequest):Promise<DocumentDraft>{const dto=await apiRequest<DocumentDraftResponse>('/documents/'+encodeURIComponent(id),{method:'PATCH',body:JSON.stringify(payload)});return mapDocumentResponse(dto)}
export async function deleteDocument(id:string):Promise<void>{await apiRequest<void>('/documents/'+encodeURIComponent(id),{method:'DELETE'})}
