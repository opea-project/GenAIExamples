import { useEffect } from "react"
import { getPrompts, promptSelector } from "../../redux/Prompt/PromptSlice"
import { useAppDispatch, useAppSelector } from "../../redux/store"
import styleClasses from './promptTemplate.module.scss'
import { userSelector } from "../../redux/User/userSlice"
type PromptTemplateProps =  {
    setPrompt: (prompt:string)=>void; 
}
function PromptTemplate({setPrompt}:PromptTemplateProps) {
    const dispatch = useAppDispatch()
    const {prompts} = useAppSelector(promptSelector)
    const {name} = useAppSelector(userSelector)
    useEffect(()=> {
        if(name && name!=="")
            dispatch(getPrompts({promptText:""}))
    },[])
  return (
      <div className={styleClasses.promptContainer}>
          Prompt Templates

          {
              prompts.map(prompt => <div className={styleClasses.prompt} onClick={async () => {
                  setPrompt(prompt.prompt_text)

              }}>{prompt.prompt_text}</div>)
          }
      </div>
  )
}

export default PromptTemplate