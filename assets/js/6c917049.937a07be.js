"use strict";(self.webpackChunkdocumentation=self.webpackChunkdocumentation||[]).push([[836],{4896:(e,n,t)=>{t.r(n),t.d(n,{assets:()=>a,contentTitle:()=>s,default:()=>p,frontMatter:()=>l,metadata:()=>o,toc:()=>c});const o=JSON.parse('{"id":"fmu/general_preparations","title":"General Preparation to Completor in FMU","description":"General Preparation to Completor in FMU","source":"@site/docs/fmu/general_preparations.mdx","sourceDirName":"fmu","slug":"/fmu/general_preparations","permalink":"/completor/fmu/general_preparations","draft":false,"unlisted":false,"editUrl":"https://github.com/equinor/completor/tree/main/documentation/docs/fmu/general_preparations.mdx","tags":[],"version":"current","sidebarPosition":2,"frontMatter":{"title":"General Preparation to Completor in FMU","sidebar_position":2,"description":"General Preparation to Completor in FMU"},"sidebar":"docs","previous":{"title":"Completor in FMU","permalink":"/completor/fmu/"},"next":{"title":"Running Completor in FMU","permalink":"/completor/fmu/run_completor"}}');var r=t(4848),i=t(8453);const l={title:"General Preparation to Completor in FMU",sidebar_position:2,description:"General Preparation to Completor in FMU"},s="General Preparation",a={},c=[{value:"Completor\xae case file",id:"completor-case-file",level:2},{value:"Tubing MSW input schedule file",id:"tubing-msw-input-schedule-file",level:2}];function d(e){const n={code:"code",h1:"h1",h2:"h2",header:"header",li:"li",ol:"ol",p:"p",...(0,i.R)(),...e.components};return(0,r.jsxs)(r.Fragment,{children:[(0,r.jsx)(n.header,{children:(0,r.jsx)(n.h1,{id:"general-preparation",children:"General Preparation"})}),"\n",(0,r.jsx)(n.h2,{id:"completor-case-file",children:"Completor\xae case file"}),"\n",(0,r.jsx)(n.p,{children:"The Completor\xae case file is required to run and being called through ERT as in the FMU workflow.\nSeveral things to be ensured before running through ERT are:"}),"\n",(0,r.jsxs)(n.ol,{children:["\n",(0,r.jsxs)(n.li,{children:["\n",(0,r.jsxs)(n.p,{children:["Save or store your case file in a clear place.\nFor example, it is common to put save in the ",(0,r.jsx)(n.code,{children:"../include/schedule"})," directory,\ntogether with the initial schedule file consists of a multi-segment well\n(MSW) model as the input schedule of Completor\xae."]}),"\n"]}),"\n",(0,r.jsxs)(n.li,{children:["\n",(0,r.jsx)(n.p,{children:"Ensure that you understand the uncertainty that you put in your reservoir model.\nFor example, changing grid structure, depths,\nand well trajectory will have an impact on your pre-processor trajectory, e.g., depths, segmentation,\nand lateral numbering.\nPlease keep it in mind that Completor will fail if the case file does not reflect the input schedule file as a result of geological uncertainties."}),"\n"]}),"\n"]}),"\n",(0,r.jsx)(n.h2,{id:"tubing-msw-input-schedule-file",children:"Tubing MSW input schedule file"}),"\n",(0,r.jsxs)(n.p,{children:["Completor\xae requires a multi-segment well (MSW) definition of the tubing as input.\nThe MSW schedule is commonly generated by your pre-processing reservoir modelling tools,\nas long as it contains the basic well definition in terms of ",(0,r.jsx)(n.code,{children:"WELSPECS"}),", ",(0,r.jsx)(n.code,{children:"WELSEGS"}),", ",(0,r.jsx)(n.code,{children:"COMPDAT"}),", and ",(0,r.jsx)(n.code,{children:"COMPSEGS"}),".\nEnsure that there is no inflow control device installed in the planned well completion."]})]})}function p(e={}){const{wrapper:n}={...(0,i.R)(),...e.components};return n?(0,r.jsx)(n,{...e,children:(0,r.jsx)(d,{...e})}):d(e)}},8453:(e,n,t)=>{t.d(n,{R:()=>l,x:()=>s});var o=t(6540);const r={},i=o.createContext(r);function l(e){const n=o.useContext(i);return o.useMemo((function(){return"function"==typeof e?e(n):{...n,...e}}),[n,e])}function s(e){let n;return n=e.disableParentContext?"function"==typeof e.components?e.components(r):e.components||r:l(e.components),o.createElement(i.Provider,{value:n},e.children)}}}]);