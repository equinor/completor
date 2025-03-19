"use strict";(self.webpackChunkdocumentation=self.webpackChunkdocumentation||[]).push([[721],{47:(e,t,n)=>{n.r(t),n.d(t,{assets:()=>c,contentTitle:()=>s,default:()=>u,frontMatter:()=>l,metadata:()=>o,toc:()=>a});const o=JSON.parse('{"id":"about/description","title":"Introduction","description":"Introduction to Completor","source":"@site/docs/about/description.mdx","sourceDirName":"about","slug":"/about/description","permalink":"/completor/about/description","draft":false,"unlisted":false,"editUrl":"https://github.com/equinor/completor/tree/main/documentation/docs/about/description.mdx","tags":[],"version":"current","sidebarPosition":1,"frontMatter":{"title":"Introduction","sidebar_position":1,"description":"Introduction to Completor"},"sidebar":"docs","previous":{"title":"How to start contributing","permalink":"/completor/contribution_guide"},"next":{"title":"Introduction","permalink":"/completor/about/description"}}');var i=n(4848),r=n(8453);const l={title:"Introduction",sidebar_position:1,description:"Introduction to Completor"},s="Description",c={},a=[];function d(e){const t={h1:"h1",header:"header",li:"li",p:"p",ul:"ul",...(0,r.R)(),...e.components};return(0,i.jsxs)(i.Fragment,{children:[(0,i.jsx)(t.header,{children:(0,i.jsx)(t.h1,{id:"description",children:"Description"})}),"\n",(0,i.jsx)(t.p,{children:"Completor\xae is a script (Python 3) for modelling wells with Inflow Control Technology into reservoir simulation and\nensemble simulation model."}),"\n",(0,i.jsx)(t.p,{children:'Completor\xae utilizes multi-segmented tubing definition generated by pre-processing tool\nand a user-defined file (called "case" file) specifying the completion design.\n(Note: The input schedule file should not contain any keywords or segment definitions related to inflow control).\nThe information in the input schedule file and the case file is processed and written to a new schedule file to\nbe included in reservoir simulators to produce prediction results with Inflow Control Technology.\nAn optional figure showing the structure of the planned well completion can be produced as an output.'}),"\n",(0,i.jsx)(t.p,{children:"Completor\xae is a flexible, robust and user-friendly tool that has been extensively tested with a range of\nreservoir models and well configurations.\nAll completion definitions must be included in the user-defined case file from the surface to the True Vertical Depth\n(TVD) of the well.\nIncluding any part of the segment structure located in the overburden\n(e.g., from the top of the reservoir to a junction or a downhole gauge).\nThis section is not altered by Completor\xae but it is required to be defined in the case file."}),"\n",(0,i.jsx)(t.p,{children:"Some options are given by the following examples:"}),"\n",(0,i.jsxs)(t.ul,{children:["\n",(0,i.jsx)(t.li,{children:"Inflow Control Technology can be implemented at any time (date) in the schedule file,\nnot only in wells that are operative from the simulation startup."}),"\n",(0,i.jsx)(t.li,{children:"In multilateral wells, laterals may be connected to a main branch at any depth,\nnot only the first segment penetrating the reservoir."}),"\n",(0,i.jsx)(t.li,{children:"Child branches in multilateral wells can be connected to the tubing- or device layer of the main branch."}),"\n"]})]})}function u(e={}){const{wrapper:t}={...(0,r.R)(),...e.components};return t?(0,i.jsx)(t,{...e,children:(0,i.jsx)(d,{...e})}):d(e)}},8453:(e,t,n)=>{n.d(t,{R:()=>l,x:()=>s});var o=n(6540);const i={},r=o.createContext(i);function l(e){const t=o.useContext(r);return o.useMemo((function(){return"function"==typeof e?e(t):{...t,...e}}),[t,e])}function s(e){let t;return t=e.disableParentContext?"function"==typeof e.components?e.components(i):e.components||i:l(e.components),o.createElement(r.Provider,{value:t},e.children)}}}]);