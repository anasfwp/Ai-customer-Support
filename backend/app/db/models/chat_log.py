@router.post("/query", response_model=ChatResponse)
async def query_question(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Answer a question using RAG"""
    session_id = request.session_id or str(uuid.uuid4())
    
    # Use the RAG pipeline to answer the question
    pipeline = RAGPipeline()
    result = pipeline.answer_question(
        db=db,
        tenant_id=current_user.tenant_id,
        question=request.question
    )
    
    # Log the chat to database
    from app.db.models.chat_log import ChatLog
    chat_log = ChatLog(
        id=str(uuid.uuid4()),
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        question=request.question,
        answer=result["answer"],
        citations=result.get("citations", []),
        confidence=str(result.get("confidence", 0.0)),
        fallback=result.get("fallback", True)
    )
    db.add(chat_log)
    db.commit()
    
    return ChatResponse(
        answer=result["answer"],
        citations=result.get("citations", []),
        confidence=result.get("confidence", 0.0),
        fallback=result.get("fallback", True),
        session_id=session_id
    )